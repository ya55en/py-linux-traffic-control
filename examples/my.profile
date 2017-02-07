; sample profile for examples

[4g-sym-egress]
clear
verbose
interface lo
upload
  tcp:dport:443:2560kbit
  tcp:dport:8080:2560kbit
  tcp:dport:8082:2560kbit
  udp:dport:10000-35000:2560kbit


[4g-sym-ingress]
clear
verbose
interface lo
download
  tcp:sport:443:2560kbit
  tcp:sport:8080:2560kbit
  tcp:sport:8082:2560kbit
  udp:sport:10000-35000:2560kbit
