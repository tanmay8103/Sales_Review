from fastapi import FastAPI
from app.api.v1 import (
    accounts,
    opportunities,
    support_requests,
    sales_review,
    calibration,
    users,
    influencers,
    influencer_engagements
)

app = FastAPI()

# Include routers
app.include_router(accounts.router)
app.include_router(opportunities.router)
app.include_router(support_requests.router)
app.include_router(sales_review.router)
app.include_router(calibration.router)
app.include_router(users.router)
app.include_router(influencers.router)
app.include_router(influencer_engagements.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 