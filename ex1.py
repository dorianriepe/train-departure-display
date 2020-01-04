from http.server import BaseHTTPRequestHandler, HTTPServer
import db1

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
 
  # GET
  def do_GET(self):
        self.send_response(200)
 
        self.send_header('Content-type','text/html')
        self.end_headers()

        message = db1.getData()
        self.wfile.write(bytes(message, "utf8"))
        return
 
def run():
  print('starting server...')
  server_address = ('127.0.0.1', 8081)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...')
  httpd.serve_forever()
  
run()