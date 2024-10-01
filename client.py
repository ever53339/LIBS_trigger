import socketio

client = socketio.Client()

client.connect('http://localhost:1234')

client.emit('pull_trigger', 'measure_button.png')

client.wait()