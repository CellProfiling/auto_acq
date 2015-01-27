import socket
import sys
import time

message = sys.argv[1]
test_string = sys.argv[2]

def recv_timeout(_socket, timeout, _test):
    # make socket non blocking
    _socket.setblocking(False)
     
    # total data in an array
    total_data=[]
    data=''
    joined_data = ''
     
    # start time
    begin=time.time()
    while _test not in joined_data and 'scanfinished' not in data:
        # if data exist, then break after timeout
        if total_data and time.time()-begin > timeout:
            break
         
        # if no data exist, then break after longer timeout
        elif time.time()-begin > timeout*2:
            break
         
        # receive data
        try:
            data = _socket.recv(8192)
            if data:
                print 'received "%s"' % data
                total_data.append(data)
                # reset start time
                begin=time.time()
                joined_data = ''.join(total_data)
            else:
                # sleep to add time difference
                time.sleep(0.1)
        except:
            pass

    # join all data to final data
    return ''.join(total_data)

# Create a TCP/IP socket

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()
     
print 'Socket Created'

#host = '127.000.000.001'
host = '130.229.43.22'
port = 8895

try:
    # Connect to the server at the port
    server_address = (host, port)
    print 'connecting to %s port %s' % server_address
    sock.connect(server_address)

    # Receive welcome reply from server
    recv_timeout(sock, 3, 'Welcome')

except socket.error:
    print 'Failed to connect to socket'
    sys.exit()

try:
    
    # Send data
    # Make compatible with Windows line breaks
    for line in message.splitlines():
        if line[-2:]=='\r\n':
            line = line
        if line[-1:]=='\n':
            line = line[:-1] + '\r\n'
        else:
            line = line + '\r\n'
        print 'sending "%s"' % line
        sock.send(line)
        time.sleep(0.2)
        recv_timeout(sock, 20, line[:-2])

    
except socket.error:
    #Send failed
    print 'Sending to server failed'
    sys.exit()
    
print 'Message sent successfully'

try:
    if test_string:
        #get reply and print
        recv_timeout(sock, 20, test_string)
        print('closing')

finally:
    time.sleep(1)
    #print 'closing socket'
    #sock.shutdown(socket.SHUT_WR)
    #sock.close()
    sys.exit()
