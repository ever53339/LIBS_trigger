import socketio

client = socketio.Client()

client.connect('http://localhost:1234')

client.emit('pull_trigger', 'pull trigger')

client.wait()