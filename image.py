import pyodbc
import os
import io
from PIL import Image
from image_matcher import JewelryMatcher

matcher = JewelryMatcher()


def get_connection(db_name='JewlDB'):
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER=DESKTOP-PTEDHKV;'
            f'DATABASE={db_name};'
            'Encrypt=no;'
            'Connect Timeout=30;'
            'Trusted_Connection=yes;'
        )
        print("Connection successful with db:", db_name)
        return conn
    except pyodbc.Error as e:
        print(f"Connection failed: {str(e)}")
        raise

    # f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            # f'SERVER=127.0.0.1;'
            # f'DATABASE={db_name};'
            # f'UID=SA;'
            # f'PWD={{lahore@17}};'
            # 'Encrypt=no;'
            # 'Connect Timeout=30;'

# Function to fetch the sold item based on filters 
def sold_stock(filters):
    """Fetch sold stock items with dynamic filtering based on provided criteria."""
    print('Filters received:', filters)
    
    # Base query without WHERE clauses
    query = """
        SELECT 
            s.TagNo,
            s.Description,
            s.SaleNo,
            s.NWeight AS [Total Net Weight],
            s.NetWeight AS [Weight],
            sa.BillInWord
        FROM 
            dbo.Stock s
        JOIN 
            dbo.Sale sa ON s.SaleNo = sa.SaleNo
    """
    
    # Dynamically build WHERE clauses and parameters
    where_clauses = []
    params = []
    
    # Helper function to add filter conditions
    def add_filter(column_name, filter_value, operator='='):
        if filter_value is not None:
            where_clauses.append(f"{column_name} {operator} ?")
            params.append(filter_value)
    
    # Apply filters
    add_filter('s.ItemId', filters.get('item_id'))
    add_filter('s.WorkerId', filters.get('worker_id'))
    add_filter('s.NWeight', filters.get('net_weight_from'), '>=')
    add_filter('s.NWeight', filters.get('net_weight_to'), '<=')
    add_filter('s.NetWeight', filters.get('weight_from'), '>=')
    add_filter('s.NetWeight', filters.get('weight_to'), '<=')
    add_filter('s.SaleDate', filters.get('date_from'), '>=')
    add_filter('s.SaleDate', filters.get('date_to'), '<=')
    
    # Combine WHERE clauses if any exist
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    print('Final query:', query)
    print('Query parameters:', params)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query, params)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Convert results to list of dictionaries
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        print(f'Found {len(results)} matching records')
        print('Result: ',results)
        return results
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        # Consider raising the exception after logging if you want calling code to handle it
        return []


# Function to match uploaded image with images in the database
def fetch_db_images(sold_items,output_folder):
    """Fetch and compare images only for TagNos in sold_items"""
    if not sold_items:
        return []

    # Get unique TagNos (using set to avoid duplicates)
    tag_nos = list({item['TagNo'] for item in sold_items})

    # Create SQL placeholders and query
    placeholders = ','.join(['?'] * len(tag_nos))
    query = f"""
    SELECT PicId, TagNo, Picture 
    FROM dbo.JewlPictures 
    WHERE TagNo IN ({placeholders})
    """

    matches = []
    try:
        conn = get_connection('JewlPics')
        cursor = conn.cursor()
        cursor.execute(query, tag_nos)

        # Create a lookup dictionary for sold items
        sold_items_lookup = {item['TagNo']: item for item in sold_items}

        for row in cursor.fetchall():
            try:
                image_id = row.PicId
                tag_no = row.TagNo
                hex_data = row.Picture


                # Process hex data more efficiently
                hex_str = hex_data.hex()[2:] if isinstance(hex_data, bytes) and hex_data.startswith(b'0x') else \
                         hex_data.hex() if isinstance(hex_data, bytes) else \
                         hex_data[2:] if isinstance(hex_data, str) and hex_data.startswith('0x') else \
                         hex_data

                # Convert to image
                image_bytes = bytes.fromhex(hex_str)
                image = Image.open(io.BytesIO(image_bytes))
                
                # Save image
                image_path = os.path.join(output_folder, f'{tag_no}_{image_id}.jpg')
                image.save(image_path)
                
                # Compare with uploaded image
                if match_result := evaluate_image_similarity(image_path):
                    matches.append({
                        **sold_items_lookup[tag_no],  # Original item data
                        'matched_image': {            # Match details
                            **match_result,
                            'TagNo': tag_no
                        }
                    })
                else:
                    os.remove(image_path)
                
            except Exception as e:
                print(f"Error processing image {image_id} for {tag_no}: {str(e)}")
    
    finally:
        conn.close()
    
    return matches


def evaluate_image_similarity(db_img,temp_path = "temp_upload.jpg"):
    if not os.path.exists(db_img):
        return {}
    score = matcher.compare(temp_path, db_img)
    if score >= 0.50:  # Match threshold
        return {
            "path": db_img.replace("\\", "/"),
            "score": float(f"{score:.2f}")
        }
    return {}

def get_items():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Item")  
    items = []
    for row in cursor.fetchall():
        temp = {
            "itemId": row.ItemId,
            "itemName": row.ItemName,
        }
        items.append(temp)
    return items

def get_worker():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Worker")  
    workers = []
    for row in cursor.fetchall():
        temp = {
            "workerId": row.WorkerId,
            "workerName": row.WorkerName,
        }
        workers.append(temp)
    return workers