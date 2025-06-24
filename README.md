Basic client and mcp server around https://access.redhat.com/management/api/case_management

# How to install

```
pip install rhsupportcli fastmcp
```

# Configure

Get an offline token from [https://access.redhat.com/management/api](https://access.redhat.com/management/api)


3. The server is started and configured differently depending on what transport you want to use

For STDIO:

In VSCode for example:
```json
   "mcp": {
        "servers": {
            "Rhsupportcli": {
                "command": "python3",
                "args": ["/path/to/rhsupportcli/src/rhsupportlib/mcp_server.py"],
                "env": {
                    "OFFLINETOKEN": <your token>
                }
            }
        }
    }
```

For Streamable HTTP:

Start the server in a terminal:

`rhcsupportmcp``

Configure the server in the client:

```json
    "rhsupportcli": {
      "transport": "streamable-http",
      "url": "http://localhost:8000"
      "headers": {
        "OFFLINETOKEN": "<your token>"
      }
    }
```
