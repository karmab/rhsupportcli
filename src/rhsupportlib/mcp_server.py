import argparse
from rhsupportlib import RHsupportClient
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers


mcp = FastMCP("rhsupportmcp")


@mcp.tool()
def create_case(parameters: dict) -> dict:
    """Create case"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.create_case(parameters)


@mcp.tool()
def create_attachment(case: str, path: str):
    """Create attachment"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.create_attachment(case, path)


@mcp.tool()
def create_comment(case: str, comment: str):
    """Create comment"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.create_comment(case, comment)


@mcp.tool()
def get_attachments(case: str, path: str = '/tmp'):
    """Get attachments"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.get_attachments(case, path)


@mcp.tool()
def get_case(case: str) -> dict:
    """Retrieve information on case"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.get_case(case)


@mcp.tool()
def list_cases(parameters: list = {}) -> list:
    """List cases"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.list_cases(parameters)


@mcp.tool()
def list_customers(account: str = None) -> list:
    """List customers"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.list_customers(account)


@mcp.tool()
def list_partners(account: str = None) -> list:
    """List partners"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.list_partners(account)


@mcp.tool()
def list_contacts(account: str = None) -> list:
    """List contacts"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.list_accounts(account)


@mcp.tool()
def search_cases(q: str) -> list:
    """Search cases"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.search_cases({'q': q})


@mcp.tool()
def search_kcs(q: str) -> list:
    """Search kcs"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.search_kcs({'q': q})


@mcp.tool()
def update_case(case: str, parameters: dict) -> dict:
    """Update case"""
    offlinetoken = get_http_headers().get('OFFLINETOKEN')
    rhc = RHsupportClient(offlinetoken)
    return rhc.update_case(case, parameters)


def main():
    parser = argparse.ArgumentParser(description="rhsupportmcp")
    parser.add_argument("--port", type=int, default=8000, help="Localhost port to listen on")
    parser.add_argument("--http", action='store_true')
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="http", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
