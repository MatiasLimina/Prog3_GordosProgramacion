from fastapi import Request

def get_product_repository(request: Request):
    return request.app.state.product_repo

def get_client_repository(request: Request):
    return request.app.state.client_repo
