from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
from .restapis import post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)

# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    if request.method == "POST":
        # Get credentials
        username = request.POST['username']
        password = request.POST['password']

        # Check credentials
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)

        return redirect('djangoapp:index')
    else:
        return redirect('djangoapp:index')

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)

    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/registration.html', context)

    elif request.method == "POST":
        # Get input data
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            pass

        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)

            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/3208dba4-4017-4ebc-99eb-6b6b1f9ccb0c/dealership-package/get-dealerships"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)

        context["dealership_list"] = dealerships
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/3208dba4-4017-4ebc-99eb-6b6b1f9ccb0c/dealership-package/review"
        # Get reviews from the URL
        reviews = get_dealer_reviews_from_cf(url, dealer_id)

        context["dealer_reviews"] = reviews
        context["dealer_id"] = dealer_id

        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    if request.method == "GET":
        context["cars"] = CarModel.objects.filter(dealer_id=int(dealer_id))
        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/3208dba4-4017-4ebc-99eb-6b6b1f9ccb0c/dealership-package/get-dealerships"
        # Get dealers from the URL
        dealers = get_dealers_from_cf(url)
        context["dealer"] = list(filter(lambda d: d.id == int(dealer_id), dealers))[0]
        return render(request, 'djangoapp/add_review.html', context)

    elif request.method == "POST":
        review = dict()

        review["time"] = datetime.utcnow().isoformat()
        review["dealership"] = dealer_id
        review["review"] = {
            "review": request.POST["content"],
        }

        if request.POST.get("purchasecheck", False):
            review["review"]["purchase_date"] = request.POST["purchasedate"]
            car = CarModel.objects.get(id=request.POST["car"])
            review["review"]["car_make"] = car.make.name
            review["review"]["car_model"] = car.model
            review["review"]["car_year"] = car.year.strftime("%Y")

        json_payload = {"review": review}

        post_request("https://eu-de.functions.appdomain.cloud/api/v1/web/3208dba4-4017-4ebc-99eb-6b6b1f9ccb0c/dealership-package/review", json_payload)

        return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
