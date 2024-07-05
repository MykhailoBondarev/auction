from django.conf import settings
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.core.validators import EmailValidator, ValidationError, validate_image_file_extension
from django.core.exceptions import ObjectDoesNotExist
from .models import User, Category, Lot, Rate, Photo, LotPhoto, Comment, Watchlist
from PIL import Image
# from django.db import connection
from markdown import markdown
  
def _crop_image(image_path, w_output, h_output):
    img = Image.open(image_path)
    width, height = img.size  # Get dimensions

    if width > w_output and height > h_output:
        # keep ratio but shrink down
        img.thumbnail((width, height))
            # check which one is smaller
        if height < width:
            # make square by cutting off equal amounts left and right
            left = (width - height) / 2
            right = (width + height) / 2
            top = 0
            bottom = height
            img = img.crop((left, top, right, bottom))

        elif width < height:
            # make square by cutting off bottom
            left = 0
            right = width
            top = 0
            bottom = width
            img = img.crop((left, top, right, bottom))

        if width > w_output and height > h_output:
            img.thumbnail((w_output, h_output))
    img.save(image_path, quality=100)    

class newLotForm(forms.Form):
    lot_name = forms.CharField(label="Lot name (64 chars max)", max_length=64, required=True)
    lot_rate = forms.FloatField(label="Initial rate", required=True, min_value=0)
    lot_pic = forms.ImageField(label="Main picture", required=True, validators=[validate_image_file_extension])
    lot_description = forms.CharField(widget=forms.Textarea(attrs={'id': 'editor', 'placeholder': 'Description (1000 chars max)'}), label=False)
    lot_category = forms.ChoiceField(label="Category", widget = forms.Select(), required=True)
    lot_photos = forms.ImageField(label="Choose lot photos", required=True, validators=[validate_image_file_extension], 
                                widget=forms.ClearableFileInput(attrs={"multiple": True}))

class addRateForm(forms.Form):
    parent_page = forms.CharField(widget=forms.HiddenInput())
    lot_rate = forms.FloatField(label=False, min_value=0, required=True, widget=forms.NumberInput(attrs={'placeholder': 'Type your bid'}))

class addCommentForm(forms.Form):
    parent_page = forms.CharField(widget=forms.HiddenInput())
    reply_to = forms.CharField(widget=forms.HiddenInput(), required=False)
    lot_comment = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Add a comment...', 'class': 'col col12', 'rows': '5'}), label=False, max_length=1000, required=True)

class updateUserInfoForm(forms.Form):
    icon = forms.ImageField(label="Icon", validators=[validate_image_file_extension], widget=forms.ClearableFileInput(attrs={'class': 'btn btn-outline-secondary'}), required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'First name', 'class': 'form-control my-3'}), label=False, max_length=64, required=True)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Last name', 'class': 'form-control my-3'}), label=False, max_length=64, required=True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder':'Email', 'class': 'form-control my-3'}), label=False, required=True)

def _dict_to_tuple(dict):
    category_list = [("", 'Choose')]
    for item in dict:
        cat_tuple = (item.id, item.name)
        category_list.append(cat_tuple)
    return tuple(category_list)

def _show_username(un, fn, ln):
    displayed_name = un
    if fn or ln:
        displayed_name = fn + " " + ln
    return displayed_name

def _show_as_int(float_num):
    if float_num - int(float_num):
        result = float_num
    else:
        result = int(float_num)
    return result

def _set_watchlist(request):
    watchlist = Watchlist.objects.filter(user_id=request.user.id)
    request.session["watchlist"] = []
    for item in watchlist:
        request.session["watchlist"].append(item.lot_id)

def _unset_watchlist(request):
    request.session["watchlist"] = []
    
def index(request):
    lots = None
    categories = None

    try:
        lots = Lot.objects.prefetch_related("commentlots").annotate(comments_count=Count("commentlots__id")).filter(active=True).order_by('-id')[:5]      
        categories = Category.objects.prefetch_related("lotcategories").filter(lotcategories__active=True).annotate(lots_count=Count("lotcategories__id")).order_by("name")
        '''     
            SELECT auctions_category.name AS name, COUNT(auctions_lot.id) AS lots_count 
            FROM auctions_category
            JOIN auctions_lot ON 
            auctions_lot.category_id = auctions_category.id
            WHERE auctions_lot.active = 1
            GROUP BY auctions_category.id  ORDER BY auctions_category.name ASC;
        ''' 

        for lot in lots:
            lot.initial_rate = _show_as_int(lot.initial_rate)

    except ObjectDoesNotExist:
        pass    
    return render(request, "auctions/index.html", {
        "categories": categories,
        "lots": lots,
        "base_url": settings.MEDIA_URL
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            username = _show_username(user.username, user.first_name, user.last_name)
            _set_watchlist(request)
            messages.success(request, f"Welcome back, {username}!")
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def logout_view(request):
    _unset_watchlist(request)
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })
        # Checking is email valid
        try:
            emailValid = EmailValidator()
            emailValid(email)
        except ValidationError:
            return render(request, "auctions/register.html", {
                "message": "Email is not valid!"
            })
        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        messages.success(request, "You have successfuly registered!")
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def my_auctions(request):
    page = "auctions/login.html"
    if request.user.is_authenticated:
        my_lots = Lot.objects.filter(author=request.user.id).order_by('-id')
        page = "auctions/auctionslist.html"

    return render(request, page, {
        "lots": my_lots,
        "base_url": settings.MEDIA_URL
    })

def new_auction(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = newLotForm(request.POST, request.FILES)
            selected_category_id = request.POST.get("lot_category")
            form.fields['lot_category'].choices = [(selected_category_id, selected_category_id)]
            lot_photos = request.FILES.getlist("lot_photos")

            if form.is_valid():
                data = form.cleaned_data
                lot = Lot()
                lot.name = data["lot_name"]
                lot.picture = data["lot_pic"]
                lot.description = markdown(data["lot_description"])
                lot.initial_rate = round(data["lot_rate"], 2)
                lot.category_id = data["lot_category"]
                lot.author_id = request.user.id
                lot.save()                
                thumbnail = lot.__dict__['picture']
                _crop_image(settings.MEDIA_ROOT + thumbnail, 150, 150)
                for photo in lot_photos:
                    photo_object = Photo.objects.create(name=photo)
                    LotPhoto.objects.create(lot=lot, photo=photo_object)
                    try:
                        image_path = settings.MEDIA_ROOT + photo_object.name.name
                        fixed_height = 700                        
                        image_obj = Image.open(image_path)
                        height_percent = (fixed_height/float(image_obj.size[1]))
                        width_size = int(float(image_obj.size[0])*float(height_percent))
                        image_obj = image_obj.resize((width_size, fixed_height), Image.NEAREST)
                        image_obj.save(image_path, quality=95)
                    except IOError:
                        print("Cannot open file!")
                messages.success(request, "Lot successfuly created!")

                return HttpResponseRedirect(reverse("my-auctions"))
            else:
                categories = Category.objects.all()
                categories_tuple = _dict_to_tuple(categories)
                form.fields['lot_category'].choices = categories_tuple
                form.fields['lot_category'].initial = [""]

                return render(request, "auctions/new_auction.html", {
                    "form": form
                })
            
        categories = Category.objects.all()
        categories_tuple = _dict_to_tuple(categories)
        new_lot_form = newLotForm()
        new_lot_form.fields['lot_category'].choices = categories_tuple
        new_lot_form.fields['lot_category'].initial = [""]       

        return render(request, "auctions/new_auction.html", {
            "form": new_lot_form 
        })
    else:
        return HttpResponseRedirect(reverse("login"))
    
def lot_view(request, lot_id):
    page = "404.html"
    lot_data = None
    lot_winner = None
    lot_author = None

    try:
        lot_info = Lot.objects.get(pk=lot_id)
        lot_author = lot_info.author_id
        lot_winner = lot_info.winner
    except ObjectDoesNotExist:
        pass 
    if request.user.is_authenticated and (request.user.id == lot_author or request.user.id == lot_winner):
        try:        
            lot_data = Lot.objects.select_related("author").filter(pk=lot_id)
        except ObjectDoesNotExist:
            pass
    else:
        try:
            lot_data = Lot.objects.select_related("author").filter(pk=lot_id, active=True)
        except ObjectDoesNotExist:
            pass

    try:
        photos = LotPhoto.objects.select_related("photo").filter(lot_id=lot_id)
    except ObjectDoesNotExist:
        pass    

    try:
        bids = Rate.objects.select_related("author").filter(lot_id=lot_id).order_by("-create_date")[:10]
    except ObjectDoesNotExist:
        pass

    try:
        comments = Comment.objects.select_related("author").filter(lot_id=lot_id).order_by("create_date")
    except ObjectDoesNotExist:
        pass

    if lot_data:
        lot_data = lot_data[0]
        del lot_data.author.password
        lot_data.initial_rate = _show_as_int(lot_data.initial_rate)
        lot_data.displayed_name = _show_username(lot_data.author.username, 
                                                        lot_data.author.first_name, lot_data.author.last_name) 
        lot_data.photos = photos
        lot_data.bids = bids
        for comment in comments:
            comment.displayed_name = _show_username(comment.author.username, comment.author.first_name,
                                                    comment.author.last_name)      
        lot_data.comments = comments

        page = "auctions/lot.html"

    return render(request, page, {
                                "lot": lot_data, 
                                "base_url": settings.MEDIA_URL,
                                "rate_form": addRateForm(initial={'parent_page': request.path}),
                                "comment_form": addCommentForm(initial={'parent_page': request.path})
                                })

def lot_activate(request):
    if request.user.is_authenticated and request.method == "POST":
        user_id = request.user.id
        lot_id = request.POST['lot-id']
        lot_active =  not eval(request.POST['lot-state'])           
        try:
            Lot.objects.filter(pk=lot_id, author_id=user_id).update(active=lot_active)            
        except ObjectDoesNotExist:
            pass
        message = f"Auction №{lot_id} closed!"
        if lot_active:
            Lot.objects.filter(pk=lot_id).update(winner=0) 
            message = f"Auction №{lot_id} started!"
        else:
            try:
                rates = Rate.objects.filter(lot=lot_id).order_by("-id")
            except ObjectDoesNotExist:
                pass

            if rates:
                winner_id = rates.first().author_id
                Lot.objects.filter(pk=lot_id).update(winner=winner_id) 

    messages.success(request, message)
    return HttpResponseRedirect(reverse("my-auctions"))

def not_found(request, any_exception):
    return render(request, "404.html", status=404)


def category_view(request, cat_id):
    page = "404.html"
    lots = None
    category = None 
    try:
        lots = Lot.objects.prefetch_related("commentlots").select_related("category").annotate(comments_count=Count("commentlots__id")).filter(category_id=cat_id, active=True)
    except ObjectDoesNotExist:
        pass

    if lots:
        page = "auctions/category-lots.html"
        category = lots[0].category
    return render(request, page, {
        "lots": lots,
        "base_url": settings.MEDIA_URL,
        "category": category
    })

def watchlist(request):
    page = "auctions/login.html"
    if request.user.is_authenticated:
        watchlist = Watchlist.objects.select_related("lot").filter(user_id=request.user.id)
        page = "auctions/watchlist.html"
        return render(request, page, {
            "watchlist": watchlist,
            "base_url": settings.MEDIA_URL,
        })
    return HttpResponseRedirect("login")

def change_watchlist(request, lot_id):
    page = "login"
    if request.user.is_authenticated:
        if request.method == "POST":

            page = request.POST.get('parent_page', "/")
            current_lot_id = None
            try:
                current_lot_id = int(lot_id)
            except ValueError:
                pass
            if current_lot_id:
                if current_lot_id in request.session["watchlist"]:
                    try:
                        Watchlist.objects.filter(lot_id=current_lot_id, user_id=request.user.id).delete()
                        messages.success(request, "Lot was successfuly removed from your watchlist")
                    except IntegrityError:
                        messages.error(request, "Lot is already deleted from your watchlist") 
                else:
                    try:
                        Watchlist.objects.create(lot_id=current_lot_id, user_id=request.user.id)                    
                        messages.success(request, "Lot was successfuly added to your watchlist")
                    except IntegrityError:
                        messages.error(request, "Lot is already in your watchlist")  
                _set_watchlist(request)
            return HttpResponseRedirect(page)
    return HttpResponseRedirect(reverse(page))

def add_rate(request):
    page = "login"
    if request.user.is_authenticated:
        if request.method == "POST":
            page = request.POST.get("parent_page", "/")
            form = addRateForm(request.POST)            
            if form.is_valid():
                data = form.cleaned_data
                lot_id = data["parent_page"].split("/")[2]
                lot_rate = round(float(data["lot_rate"]), 2)                
                rate_request = Lot.objects.get(pk=lot_id)
                if rate_request.initial_rate <= lot_rate:
                    Lot.objects.filter(pk=lot_id).update(initial_rate=lot_rate)
                    rate = Rate()
                    rate.rate = lot_rate
                    rate.author_id = request.user.id
                    rate.lot_id = lot_id
                    rate.save()                 
                    messages.success(request, "Thank you. Your bid has been accepted.")
                else:
                   messages.error(request, "Your bid is too low.") 
            else:
                messages.error(request, "Your bid is invalid!")
        return HttpResponseRedirect(page)
    return HttpResponseRedirect(reverse(page))

def add_comment(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            page = request.POST.get("parent_page", "/")
            form = addCommentForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data    
            comment = Comment()
            comment.lot_id = data["parent_page"].split("/")[2]
            comment.comment = data["lot_comment"]
            comment.author_id = request.user.id
            if data["reply_to"]:
                try:
                    data["reply_to"] = int(data["reply_to"])
                    comment.reply_to = data["reply_to"]
                except ValueError:
                    messages.error(request, "Sorry, but you can`t reply to this comment") 
                    return HttpResponseRedirect(page)                                    
            comment.save()
            messages.success(request, "Thank you. For your comment!")
        else:
            messages.error(request, "Your comment is empty") 
        return HttpResponseRedirect(page)
    
def profile(request):
    page = "auctions/login.html"
    form = None
    if request.user.is_authenticated:
        old_icon_path = ''
        user_id = request.user.id
        fn = request.user.first_name
        ln = request.user.last_name
        em = request.user.email
        form = updateUserInfoForm(initial={'first_name': fn, 'last_name': ln, 'email': em})    
        page = "auctions/profile.html"
        if request.method == "POST":
            form = updateUserInfoForm(request.POST, request.FILES)
            if form.is_valid():
                form_data = form.cleaned_data                
                user = User.objects.get(pk=user_id)
                user.first_name = form_data['first_name']
                user.last_name = form_data['last_name']
                if form_data['icon']:
                    user.icon = form_data['icon']
                user.email = form_data['email']
                user.save()
                if form_data['icon']:
                    icon_path = settings.MEDIA_ROOT + user.__dict__['icon']
                    _crop_image(icon_path, 100, 100)

                    if request.user.icon and request.user.icon != 'no-icon.jpg':
                        old_icon_path = settings.MEDIA_ROOT + request.user.icon.name

                    # deleting an old uploaded image
                    if os.path.exists(old_icon_path):
                        os.remove(old_icon_path)
                
                messages.success(request, "Your info has been updated!")
                return HttpResponseRedirect('profile') 
    return render(request, page, {
        "base_url": settings.MEDIA_URL,
        "user_form": form
    })

def search(request):
    query = request.GET.get('q').strip(" ")

    if query:
        lots = Lot.objects.prefetch_related("commentlots").annotate(
            comments_count=Count("commentlots__id")
        ).filter(
            Q(name__icontains=query.lower()) | Q(description__icontains=query.lower()) |
            Q(name__icontains=query.upper()) | Q(description__icontains=query.upper()) |
            Q(name__icontains=query.capitalize()) | Q(description__icontains=query.capitalize()), 
            active=True)
        
        categories = []
        for lot in lots:
            if lot.category.name not in categories:
                categories.append(lot.category.name)
    else:
        return HttpResponseRedirect('/')

    return render(request, "auctions/search.html", {
        "base_url": settings.MEDIA_URL,
        "lots": lots,
        "categories": categories,
        "query": query         
    }) 