import socketio

a = socketio.Client()



@a.event
def connect():
    print("I'm connected!")

@a.event
def connect_error(data):
    print("The connection failed!")

@a.event
def disconnect():
    print("I'm disconnected!")

def status_hd(data):
    print(data)
    print('received data')
    
a.on('status', status_hd)


# a.connect('http://localhost:8080')
a.connect('http://localhost:1234')
# b = a.emit('get_status', 'data', callback=my_callback)
# print(b)
# c = a.emit('get_status_options', data=None)
# print(c)
a.wait()