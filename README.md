# Webproxy

A simple HTTP/1.0 Web proxy server that passes data between a web client and a web server

## Usage

```
python Webproxy.py <port>
```

## Feature

- Simple caching. A typical proxy server will cache the web pages each time the client makes a particular request for the first time. 
- Advanced caching. A proxy server must verify that the cached objects are still valid and that they are the correct responses to the client’s requests.
- Text censorship. A text file censor.txt containing a list of censored words is placed in the same directory as your WebProxy.
- Multi-threading. Your proxy can concurrently handle multiple connections from several clients.