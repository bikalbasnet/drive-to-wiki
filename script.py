import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Path to the credentials JSON file for the Google Drive API
credentials_path = 'secret-key.json'

# ID of the folder in Google Drive containing the Google Docs
folder_id = '1fONm32G4L2I3XmjEtCXSCc4iDahY7r5K'

# Set up the Google Drive API client
scopes = ['https://www.googleapis.com/auth/drive.readonly']
credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
drive_service = build('drive', 'v3', credentials=credentials)

def download_google_doc(google_doc_id):
    # Create a temporary directory to store the downloaded file
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)

    # Download the Google Doc as a HTML file
    request = drive_service.files().export_media(fileId=google_doc_id, mimeType='text/html')
    file_path = os.path.join(temp_dir, f'{google_doc_id}.html')

    with open(file_path, 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

    return file_path

def create_html_pages_from_folder(folder_id, output_dir):
    # Retrieve the list of files in the folder
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()
    files = results.get('files', [])

    if not files:
        print("No files found in the folder.")
        return

    # Process each file in the folder
    for file in files:
        file_id = file['id']
        file_name = file['name']
        file_mime_type = file['mimeType']

        # Check if the file is a Google Doc
        if file_mime_type == 'application/vnd.google-apps.document':
            print(f"Processing Google Doc: {file_name}")

            # Download the Google Doc as a HTML file
            html_file_path = download_google_doc(file_id)

            # Read the content of the HTML file
            with open(html_file_path, 'r') as html_file:
                html_content = html_file.read()

            # Create the HTML page
            html_page = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>{file_name}</title>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            '''

            # Save the HTML page to the output directory
            output_file_path = os.path.join(output_dir, f'{file_name}.html')
            with open(output_file_path, 'w') as output:
                output.write(html_page)

            # Delete the temporary HTML file
            os.remove(html_file_path)

        # Check if the file is a folder
        elif file_mime_type == 'application/vnd.google-apps.folder':
            print(f"Processing folder: {file_name}")

            # Create a corresponding folder in the output directory
            folder_path = os.path.join(output_dir, file_name)
            os.makedirs(folder_path, exist_ok=True)

            # Recursively process the files inside the folder
            create_html_pages_from_folder(file_id, folder_path)

        else:
            print(f"Skipping file: {file_name} (Unsupported file type)")

    print("HTML pages created successfully.")

def create_wiki_style_html(output_dir, output_file):
    # Generate the left panel navigation
    def generate_navigation(directory):
        files = []
        folders = []

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and item.endswith('.html'):
                files.append(item)
            elif os.path.isdir(item_path):
                folders.append(item)

        navigation = '<ul>\n'
        for folder in folders:
            folder_path = os.path.join(directory, folder)
            navigation += f'<li><strong>{folder}</strong>\n'
            navigation += generate_navigation(folder_path)
            navigation += '</li>\n'

        for file in files:
            file_path = os.path.join(directory, file)
            file_name = os.path.splitext(file)[0]
            navigation += f'<li><a href="{file_path}">{file_name}</a></li>\n'

        navigation += '</ul>\n'

        return navigation

    # Generate the HTML page with the left panel navigation
    html_page = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wiki-style HTML</title>
        <style>
        body {{
            display: flex;
        }}
        #navigation {{
            width: 20%;
            background-color: #f1f1f1;
            padding: 10px;
            border-right: 1px solid #ddd;
        }}
        #content {{
            flex: 1;
            padding: 10px;
        }}
        </style>
    </head>
    <body>
        <div id="navigation">
            <h3>Navigation</h3>
            {generate_navigation(output_dir)}
        </div>
        <div id="content">
            <h1>Welcome to the Wiki</h1>
        </div>
    </body>
    </html>
    '''

    # Save the HTML page to the output file
    with open(output_file, 'w') as output:
        output.write(html_page)



# Example usage
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)
create_html_pages_from_folder(folder_id, output_dir)

output_file = 'wiki.html'
create_wiki_style_html(output_dir, output_file)