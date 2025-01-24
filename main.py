import secrets

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown import markdown
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from database import get_db, Base, engine
from models.admins import Admins
from models.blog import Blog
from models.images import Image
from models.reviews import Reviews
from models.users import Users
from schema.contact_DTO import ContactForm
from schema.reviews_DTO import ReviewDTO
from schema.send_notifications_DTO import SendNotificationDTO
from schema.user_DTO import CreateUserDTO
from services import review_service, image_service
from services.admin_service import create_default_admin
from services.auth_service import verify_password, hash_password
from services.contact_service import send_email
from services.image_service import get_all_images
from services.review_service import get_all_reviews
from services.send_notification import send_notifications
from services.user_service import create_user

app = FastAPI(
    title="Santa Monica Detailers API",
    description="API documentation for Santa Monica Detailers services",
    version="1.0.4",
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url=None
)
security = HTTPBasic()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        create_default_admin(db)
    finally:
        db.close()


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse("error.html", {"request": request, "error": exc.detail},
                                      status_code=exc.status_code)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("error.html", {"request": request, "error": "An unexpected error occurred."},
                                      status_code=500)


# Helper Functions
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "aquapowers" or credentials.password != "adminpanel":
        return RedirectResponse(url="/not-allowed", status_code=303)


def get_current_admin(request: Request, db: Session):
    user = request.session.get("user")
    if not user:
        return None
    return db.query(Admins).filter(Admins.username == user["username"]).first()


async def is_admin(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized Access - Admin Only"
        )
    return admin


@app.get("/", response_class=HTMLResponse, tags=['Main Router'])
async def home_page(request: Request, db: Session = Depends(get_db)):
    try:
        reviews = review_service.get_all_reviews(db)
        return templates.TemplateResponse("index.html", {"request": request, "reviews": reviews})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})


@app.get("/admin", response_class=HTMLResponse, tags=['Admin Router'])
async def admin_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return templates.TemplateResponse("admin_panel.html", {"request": request, "user": admin})


@app.get("/services", response_class=HTMLResponse, tags=['Main Router'])
async def services_page(request: Request):
    return templates.TemplateResponse("our_package.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse, tags=['Main Router'])
async def contact_us_page(request: Request):
    return templates.TemplateResponse("contact_us.html", {"request": request})


@app.post("/contact", tags=['Main Router'])
async def handle_contact_form(contact_form: ContactForm, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(Users).filter(Users.email == contact_form.email).first()
        if not existing_user:
            create_user(
                dto=CreateUserDTO(email=contact_form.email, fullname=contact_form.name),
                db=db
            )
        send_email(
            name=contact_form.name,
            email=contact_form.email,
            phone=contact_form.phone,
            message=contact_form.message
        )
        return JSONResponse(content={"success": True, "message": "Your request has been sent!"})
    except Exception as e:
        return JSONResponse(
            content={"success": False, "message": f"An error occurred: {str(e)}"},
            status_code=500
        )


@app.get("/blog", response_class=HTMLResponse, tags=['Main Router'])
async def blog_page(request: Request, db: Session = Depends(get_db)):
    articles = db.query(Blog).order_by(Blog.created_at.desc()).all()
    return templates.TemplateResponse("blog.html", {"request": request, "articles": articles})


@app.get("/blog/{slug}", tags=['Main Router'])
async def blog_page(request: Request, slug: str, db: Session = Depends(get_db)):
    try:
        article = db.query(Blog).filter(Blog.title == slug).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found.")

        html_content = markdown(article.content, extensions=["fenced_code", "tables"])
        return templates.TemplateResponse(
            "article.html", {"request": request, "article": article, "content": html_content}
        )
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})


@app.get("/reviews", response_class=HTMLResponse, tags=['Main Router'])
async def review_page(request: Request, db: Session = Depends(get_db)):
    reviews = review_service.get_all_reviews(db)
    return templates.TemplateResponse("reviews.html", {"request": request, "reviews": reviews})


@app.get("/portfolio", response_class=HTMLResponse, tags=['Main Router'])
async def portfolio_page(request: Request, db: Session = Depends(get_db)):
    images = image_service.get_all_images(db)
    return templates.TemplateResponse("portfolio.html", {"request": request, "images": images})


@app.get("/privacy-policy", response_class=HTMLResponse, tags=['Main Router'])
async def terms_policy_page(request: Request):
    return templates.TemplateResponse("terms_policy.html", {"request": request})


@app.post("/add/review", tags=['Admin Router'])
async def create_review(dto: ReviewDTO, db: Session = Depends(get_db)):
    return review_service.create_review(dto=dto, db=db)


@app.get("/add/review", response_class=HTMLResponse, tags=['Admin Router'])
async def add_review_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return templates.TemplateResponse("add_review.html", {"request": request, "user": admin})


@app.post("/add/blog", tags=['Admin Router'])
async def add_blog(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        content_str = contents.decode('utf-8')

        title = file.filename.rsplit('.', 1)[0]

        existing_article = db.query(Blog).filter(Blog.title == title).first()
        if existing_article:
            raise HTTPException(status_code=400, detail="An article with this title already exists.")

        new_article = Blog(title=title, content=content_str)
        db.add(new_article)
        db.commit()
        db.refresh(new_article)

        return templates.TemplateResponse("add_blog.html", {"request": request})

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 encoded file.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload and save the article: {e}")


@app.get("/add/blog", response_class=HTMLResponse, tags=['Admin Router'])
async def create_article_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return templates.TemplateResponse("add_blog.html", {"request": request, "user": admin})


@app.get("/add/image", response_class=HTMLResponse, tags=['Admin Router'])
async def add_image_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return templates.TemplateResponse("upload_image.html", {"request": request, "user": admin})


@app.post("/add/image", tags=['Admin Router'])
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_url = image_service.save_image(file)
        image_service.create_image_record(db, file_url)
        return RedirectResponse(url="/add/image", status_code=303)
    except Exception as e:
        return JSONResponse(
            content={"success": False, "message": f"An error occurred while uploading the image: {str(e)}"},
            status_code=500
        )


@app.get("/admin/register", response_class=HTMLResponse, tags=['Auth Router'])
async def register_admin_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/admin/register", tags=['Auth Router'])
async def register_admin(request: Request,
                         username: str = Form(...),
                         password: str = Form(...),
                         db: Session = Depends(get_db)
                         ):
    if db.query(Admins).filter(Admins.username == username).first():
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already taken. Please choose another one."
        })

    new_admin = Admins(username=username, password=hash_password(password))
    db.add(new_admin)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)


@app.delete("/delete/blog{slug}", status_code=204)
async def delete_blog(slug: str, db: Session = Depends(get_db)):
    try:
        article = db.query(Blog).filter(Blog.title == slug).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found.")

        db.delete(article)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete the article.") from e



@app.get("/delete/reviews", response_class=HTMLResponse, tags=['Admin Router'])
async def show_reviews_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)

    reviews = get_all_reviews(db)

    return templates.TemplateResponse("delete_review.html", {
        "request": request,
        "user": admin,
        "reviews": reviews
    })


@app.get("/delete/reviews/{review_id}", response_class=HTMLResponse, tags=['Admin Router'])
async def delete_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Reviews).filter(Reviews.id == review_id).first()
    if review:
        db.delete(review)
        db.commit()
        return RedirectResponse("/success_deleted", status_code=303)
    raise HTTPException(status_code=404, detail="Review not found")


@app.get("/delete/image", response_class=HTMLResponse, tags=['Admin Router'])
async def delete_image_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)

    images = get_all_images(db)

    return templates.TemplateResponse("delete_image.html", {
        "request": request,
        "user": admin,
        "images": images
    })


@app.post("/delete/image", response_class=HTMLResponse, tags=['Admin Router'])
async def delete_image(request: Request, image_id: int = Form(...), db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if image:
        db.delete(image)
        db.commit()
        return RedirectResponse(url="/success_deleted", status_code=303)
    return {"error": "Image not found"}


@app.get("/send_notification", response_class=HTMLResponse, tags=['Admin Router'])
async def notification_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return templates.TemplateResponse("send_notification.html", {"request": request, "user": admin})


@app.post("/send_notification", tags=['Admin Router'])
async def send_notification(subject: str = Form(...), body: str = Form(...), db: Session = Depends(get_db)):
    send_notifications(db, SendNotificationDTO(subject=subject, body=body))
    return RedirectResponse(url="/email_sent", status_code=303)


@app.get("/login", response_class=HTMLResponse, tags=['Auth Router'])
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", tags=['Auth Router'])
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(Admins).filter(Admins.username == username).first()
    if not admin or not verify_password(password, admin.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    request.session["user"] = {"username": admin.username, "role": "admin"}
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/success_deleted", response_class=HTMLResponse, tags=['Auth Router'])
async def success_deleted_page(request: Request):
    return templates.TemplateResponse("success_deleted.html", {"request": request})


@app.get("/email_sent", response_class=HTMLResponse, tags=['Auth Router'])
async def email_sent_page(request: Request):
    return templates.TemplateResponse("success_email_send.html", {"request": request})


@app.get("/logout", tags=['Auth Router'])
async def logout_page(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/access_denied", response_class=HTMLResponse, tags=['Auth Router'])
async def access_denied_page(request: Request):
    return templates.TemplateResponse("access_denied.html", {"request": request})


@app.exception_handler(404)
async def not_found_page(request: Request, exc: Exception):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.get("/swagger", response_class=HTMLResponse, include_in_schema=False, tags=['Admin Router'])
async def swagger_ui_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        return RedirectResponse(url="/access_denied", status_code=303)
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Swagger UI - Santa Monica Detailers"
    )


@app.get("/meta.json")
async def metadata():
    return {
        "name": "Santa Monica Detailers",
        "description": "Professional Car Detailing Services in Santa Monica. We provide premium interior and exterior detailing, paint protection, and ceramic coating for a spotless car.",
        "keywords": [
            "Santa Monica Car Detailing",
            "Santa Monica Auto Spa",
            "Santa Monica Car Wash",
            "Car Detailing",
            "Ceramic Coating Santa Monica",
            "Interior Cleaning Santa Monica",
            "Exterior Detailing Santa Monica",
            "Luxury Car Detailing Santa Monica",
            "Mobile Car Detailing Santa Monica",
            "Paint Protection Santa Monica",
            "Detailing Services",
            "Santa Monica Car Interior Cleaning",
            "Santa Monica Auto Detailing",
            "Eco-Friendly Car Wash",
            "Hand Car Wash Santa Monica"
        ],
        "author": "Santa Monica Detailers Team",
        "contact": {
            "email": "contact@santamonicadetailers.com",
            "phone": "+1 (262) 309-9545",
            "address": "1948 20th st, Santa Monica, CA"
        },
        "version": "2.0.0",
        "date_created": "2025-01-23",
        "license": "MIT",
        "social_links": {
            "facebook": "https://www.facebook.com/santamonicadetailers",
            "twitter": "https://twitter.com/santamonicadetailers",
            "instagram": "https://www.instagram.com/santamonicadetailers"
        },
        "support": {
            "faq_url": "https://www.santamonicadetailers.com/faq",
            "contact_url": "https://www.santamonicadetailers.com/contact"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
