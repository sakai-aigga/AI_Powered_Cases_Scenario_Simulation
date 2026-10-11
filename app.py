from flask import Flask

# Initialize the Flask application instance
app = Flask(__name__)

# Define the default root route
@app.route("/")
def hello_world():
    return "<h1>Hello, World!</h1>"

# Run the development server if the script is executed directly
if __name__ == "__main__":
    app.run(debug=True)
