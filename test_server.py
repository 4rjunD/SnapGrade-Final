from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    print('Starting test server on 127.0.0.1:8080')
    try:
        app.run(host='127.0.0.1', port=8080, debug=True)
    except Exception as e:
        print(f'Error starting server: {e}')
        import traceback
        traceback.print_exc()