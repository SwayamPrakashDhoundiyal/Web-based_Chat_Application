const socket = io.connect("http://192.168.0.102:5000");

            socket.on('connect', function () {
                socket.emit('join_room', {
                    username: "{{ username }}",
                    room: "{{ room }}"
                });
            })