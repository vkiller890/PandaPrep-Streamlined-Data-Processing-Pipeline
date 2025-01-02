from flask import Flask, request, render_template, send_file
import pandas as pd
import io
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import base64
import os

app = Flask(__name__)

# Ensure the downloads directory exists
os.makedirs('downloads', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clean', methods=['POST'])
def clean_data():
    try:
        # Retrieve uploaded file
        file = request.files['file']
        if not file:
            return "No file uploaded", 400

        try:
            # Read the CSV file with UTF-8 encoding using the python engine
            df = pd.read_csv(file, on_bad_lines='skip', engine='python')
        except UnicodeDecodeError:
            # If UTF-8 fails, try with ISO-8859-1 encoding
            file.seek(0)  # Reset file pointer to the beginning
            df = pd.read_csv(file, encoding='ISO-8859-1', on_bad_lines='skip', engine='python')

        # Data Cleaning
        df.fillna(value='N/A', inplace=True)  # Fill missing values
        df.drop_duplicates(inplace=True)  # Remove duplicates

        # Generate cleaned data preview (first 10 rows)
        cleaned_preview = df.head(1000000).to_html(classes='styled-table', index=False)

        # Summary Statistics
        numeric_summary = df.describe().transpose()
        numeric_summary.reset_index(inplace=True)
        if numeric_summary.shape[1] == 8:
            numeric_summary.columns = ['Column', 'Count', 'Mean', 'Std', 'Min', '25%', '50%', '75%', 'Max']
        else:
            numeric_summary.columns = ['Column'] + [f'Stat_{i}' for i in range(1, numeric_summary.shape[1])]

        stats_preview = numeric_summary.to_html(classes='styled-table', index=False)

        # Data Visualization (example: column distribution)
        fig, ax = plt.subplots(figsize=(8, 6))
        if not df.select_dtypes(include=['number']).empty:
            df.select_dtypes(include=['number']).mean().plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title('Mean of Numeric Columns', fontsize=14)
            ax.set_ylabel('Mean Value', fontsize=12)
            plt.tight_layout()

            # Save plot to a string buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            chart_html = f'<img src="data:image/png;base64,{base64.b64encode(buf.read()).decode()}" alt="Chart">'
            buf.close()

            # Save plot to a file in the downloads directory
            graph_path = os.path.join('downloads', 'mean_numeric_columns.png')
            plt.savefig(graph_path)
            plt.close(fig)
        else:
            chart_html = "<p>No numeric columns available for visualization.</p>"

        # Save cleaned data for download
        cleaned_data_path = os.path.join('downloads', 'cleaned_data.csv')
        df.to_csv(cleaned_data_path, index=False)

        # Provide a downloadable link
        download_link = "/download"
        download_graph_link = "/download-graph"

        return render_template(
            'result.html',
            cleaned_preview=cleaned_preview,
            stats_preview=stats_preview,
            chart_html=chart_html,
            download_link=download_link,
            download_graph_link=download_graph_link
        )
    except Exception as e:
        return f"An error occurred while processing the file: {str(e)}"

@app.route('/download')
def download_cleaned_data():
    return send_file(
        os.path.join('downloads', 'cleaned_data.csv'),
        as_attachment=True,
        download_name="cleaned_data.csv"
    )

@app.route('/download-graph')
def download_graph():
    return send_file(
        os.path.join('downloads', 'mean_numeric_columns.png'),
        as_attachment=True,
        download_name="mean_numeric_columns.png"
    )

if __name__ == '__main__':
    app.run(debug=True)