from fastapi import APIRouter, Header, Request, Response
from typing import Union
from datatypes import *
import logging
import hmac


router = APIRouter()
@router.post("/webhook/", response_model=WebhookResponse, status_code=200)
async def webhook(
    webhook_input: Union[WebhookPing, WebhookPush, ManualRebuild],
    request: Request,
    response: Response,
    content_length: int = Header(...),
    x_hook_signature: str = Header(None),
    x_github_event: str = Header(None)
):
    logger = logging.getLogger(request.app.state.app_name)    
    if content_length > 1_000_000:
        # To prevent memory allocation attacks
        logger.error(f"Content too long ({content_length})")
        response.status_code = 400
        return {"result": "Content too long"}
    if x_hook_signature:
        raw_input = await request.body()
        input_hmac = hmac.new(
            key=request.app.state.secret.encode(),
            msg=raw_input,
            digestmod="sha512"
        )
        if not hmac.compare_digest(
                input_hmac.hexdigest(),
                x_hook_signature
        ):
            logger.error("Invalid message signature")
            response.status_code = 400
            return {"result": "Invalid message signature"}
        logger.info("Message signature checked ok")
    else:
        logger.info("No message signature to check")
    
    logger.info(f"Event type: {x_github_event}")
    if x_github_event == "ping":
        return {"result": "ok"}
    elif x_github_event == "push":        
        request.app.state.queue.put(webhook_input)
        return {"result": "ok"}        
    logger.error(f"Unhandled event: {x_github_event}")    
