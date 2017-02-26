; Sample profile.

; Illustrates limiting HTTPS traffic and a UDP port range on a client
; machine.
;
; Notice the use  of 'rport', as we know the ports the server uses, but
; probably not the ports the local client will use.

; 4G connection, upload only
[4g-upload]
clear
verbose
interface eth0
upload
  tcp:rport:443:512kbit:2%
  udp:rport:10000-35000:512kbit:2%

; 4G connection, download only
[4g-download]
clear
verbose
interface eth0
download
  tcp:rport:443:2560kbit:2%
  udp:rport:10000-35000:2560kbit:2%

; 4G connection, upload and download
[4g]
clear
verbose
interface eth0
upload
  tcp:rport:443:512kbit:2%
  udp:rport:10000-35000:512kbit:2%
download
  tcp:rport:443:2560kbit:2%
  udp:rport:10000-35000:2560kbit:2%

; DSL, poor connection.
[dsl-poor]
clear
verbose
interface eth0
upload
  tcp:rport:443:512kbit:1%
  udp:rport:10000-35000:512kbit:1%
download
  tcp:rport:443:2mbit:1%
  udp:rport:10000-35000:2mbit:1%

; DSL, good connection
; Notice that no jitter/loss is provided, so it will be 0%
[dsl-good]
clear
verbose
interface eth0
upload
  tcp:rport:443:1mbit
  udp:rport:10000-35000:1mbit
download
  tcp:rport:443:8mbit
  udp:rport:10000-35000:8mbit

; DSL, excellent connection
[dsl-excellent]
clear
verbose
interface eth0
upload
  tcp:rport:443:5mbit
  udp:rport:10000-35000:5mbit
download
  tcp:rport:443:40mbit
  udp:rport:10000-35000:40mbit

; An example of how to completely block selective outbound traffic -- this
; particular configuration can be used to force WebRTC failures on a client
; machine.
[kill-webrtc]
clear
verbose
interface eth0
upload
  tcp:rport:3478:1kbit:100%
  udp:rport:1024-65535:1kbit:100%

; Clear the interface.
[clear]
clear
verbose
interface eth0

; vi: ft=dosini

