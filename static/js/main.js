'use strict';
"File name: main.js";
"Student Number: 22033329";

function getBasket() {
    // Get and parse the shopping basket
    return localStorage.getItem("shoppingCart") ? JSON.parse(localStorage.getItem("shoppingCart")) : []; 
}

async function makeAPICall(url, content) {
    // Make an API call based on what URL is sent to us. content is always json to send to server
    let response = await fetch(window.location.origin + "/api/v1/" + url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      redirect: "follow",
      credentials: "same-origin",
      body: JSON.stringify(content)
    });
  
    if (!response.ok) throw response.status;
    return response.json();
}

async function getBasketInfo(basketContent) {
  // get infomation about the items found in the shopping basket from the webserver
  return await makeAPICall("GetItemsData", basketContent);
}

async function createNewTransaction(basketContent) {
  // Make new transaction content with restapi 
  return await makeAPICall("MakeTransactionContext", basketContent);
}

function createNotification(imgUrl, title, desc) {
  // Create a toast notification
  let newToast = document.createElement("div");
  newToast.className = "toast";
  // Based on https://getbootstrap.com/docs/5.0/components/toasts/
  newToast.innerHTML = `
    <div class="toast-header">
      <img src="${imgUrl}" alt="${title}" class="rounded me-2 icon-size">
      <strong class="me-auto">${title}</strong>
      <button class="btn-close" data-bs-dismiss="toast" type="button"></button>
    </div>
    <div class="toast-body">${desc}</div>
  `;

  // Place the toast and wrap it in a bootstrap Toast class
  document.getElementById("toastContainer").appendChild(newToast);
  new bootstrap.Toast(newToast).show();
}

function toggleBasketBadge() {
  // Create or delete the basket icon
  let basketIcon = document.getElementById("basketIcon");
  let badge = basketIcon.querySelector('.badge');

  if (badge === null) {
    badge = document.createElement('span');
    badge.className = "badge rounded-pill badge-notification bg-danger";
    badge.innerHTML = "!";

    basketIcon.appendChild(badge);
  } else {
    basketIcon.removeChild(badge);
  }
}

function onPageLoaded() {
  // Enable global rendering of tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  });

  // Enable animations
  AOS.init();

  // Check if we have stuff in the basket. If so, show this
  let isBasket = getBasket().length > 0;

  if (isBasket === true) {
    toggleBasketBadge();
  }

  // Set the searchButton to trigger the modal
  document.getElementById("searchButton").addEventListener('click', () => {
    let modal = new bootstrap.Modal(document.getElementById('searchModal'));
    modal.toggle();
  });

  // Set the inner filter button to actual do searching
  document.getElementById("filterButton").addEventListener('click', searchQuery);
}

function addToBasket(productId, options=[]) {
  // Get current basket
  let basketContents = getBasket();
  let originalLength = basketContents.length;

  // Add this product to the basket with said options
  basketContents.push( {itemId: productId, options: options } );

  // Send a notification and update the basket icon if it is first item in basket
  createNotification("/static/product/" + productId + ".jpg", "Added!", "Item has been added to basket");
  if (originalLength <= 0) toggleBasketBadge();

  // Ammend the local storage version
  localStorage.setItem("shoppingCart", JSON.stringify(basketContents));
}

function populateBasket(basketInfo, body) {
  // Remove the loading symbol
  body.innerHTML = "";

  let basketTotalPrice = 0.0;

  for (let item of basketInfo) {
    // Update the price
    basketTotalPrice += item.productPrice;

    let optionsAsString = item.options.map((element) => element.optionName).join(", ");

    let newCard = document.createElement("div");
    newCard.className = "card mb-3";
    newCard.innerHTML = `
      <div class="row g-0">
        <div class="col-md-4">
          <img class="img-fluid rounded-start" src="/static/product/${item.productId}.jpg" alt="${item.productName}">
        </div>
        <div class="col-md-8">
          <div class="card-body">
            <h5 class="card-title">${item.productName}</h5>
            <p class="card-text text-truncate">${item.productDescription}</p>
            <p class="card-text"><strong>Options: ${optionsAsString}</strong> </p>
            <p class="card-text product-value" data-productvalue="${item.productPrice}"><strong>£${item.productPrice.toFixed(2)}</strong></p>
          </div>
        </div>
      </div>
    `;

    let cardBody = newCard.querySelector(".card-body");

    // Create a dismiss button
    let dismiss = document.createElement("button");
    dismiss.className = "btn-close text-reset float-end";
    cardBody.insertBefore(dismiss, cardBody.firstChild);

    // Finally, add the new card to the DOM
    body.appendChild(newCard);
    
    // Allow us to click the remove item button
    dismiss.addEventListener('click', () => {
      removeItem( {"itemId": item.productId, "options": [item.options]}, newCard );
    });
  }

  // Create our price counter and to checkout
  let priceElement = document.createElement("div");
  priceElement.className = "row";
  priceElement.innerHTML = `
    <div class="col-6">
      <p class="float-start" id="basketPrice" data-currenttotal="${basketTotalPrice}"><strong>Total Price: £${basketTotalPrice.toFixed(2)}</strong></p>
    </div>
    <div class="col-6">
      <button class="btn btn-success float-end" onclick="checkout()">
        <i class="bi bi-cart text-dark"></i>
        Checkout
      </button>
    </div>
  `;
  body.appendChild(priceElement);
}

function removeItem(item, domElement) {
  // item should be represented {"itemId": id, "options": []}

  // Update the basket first
  let basket = getBasket();
  basket.splice(basket.indexOf(item), 1);
  localStorage.setItem("shoppingCart", JSON.stringify(basket));

  // Update the total price now this product has been removed if still more than one item
  let basketPriceElement = document.getElementById("basketPrice");
  let price = parseFloat(domElement.querySelector(".product-value").getAttribute("data-productvalue"));
  let newTotal = parseFloat(basketPriceElement.getAttribute("data-currenttotal")) - price;
  basketPriceElement.innerHTML = `<strong>Total Price: £${newTotal.toFixed(2)}</strong>`;

  // Update internal 'total price'
  basketPriceElement.setAttribute("data-currenttotal", newTotal);

  
  // If the basket is now 0, remove the basket badge
  if (basket.length <= 0) toggleBasketBadge();

  // Then remove the card representing it
  domElement.parentNode.removeChild(domElement);
}

function triggerBasket() {
  // Show the offcanvas and attempt to get data about items from server
  let offcanvas = document.getElementById("offcanvasBasket");
  let hasBeenToggled = bootstrap.Offcanvas.getOrCreateInstance(offcanvas).toggle();

  let body = offcanvas.querySelector('.offcanvas-body');

  // Show a spinner while we are loading
  if (hasBeenToggled === false) {
    body.innerHTML = '<div class="spinner-border"></div>';
    return;
  } 

  let basket = getBasket();

  if (basket.length <= 0) {
    body.innerHTML = "There's nothing in your basket!";
    return;
  }

  getBasketInfo(basket)
    .then((result) => populateBasket(result, body))
    .catch(() => {
      body.innerHTML = "Oops, something went wrong :(";
      return;
    });
}

function checkout() {
  // Get basket
  let basket = getBasket();

  // Quit if the basket is size 0
  if (basket.length <= 0) return;

  createNewTransaction(basket)
    .then((result) => {
      // wipe the user's basket
      localStorage.removeItem("shoppingCart");
      // Change the window to the transaction window
      window.location = window.location.origin + "/purchase?id=" + result.transactionId;
    }).catch((err) => {
      if (err === 401) {
        window.location = window.location.origin + "/login"
      } else {
        console.log(err)
      }
    })
}

function formatQueryResult(result) {
  // Gets the query response and renders it based on return order
  let returnOrder = document.getElementById("sortBy").value;

  // Get DOM element we wil be making cards into
  let domElement = document.getElementById("searchContainer");

  // Destroy elements that are already there
  for (let toDestroy of domElement.querySelectorAll(".search-result")) toDestroy.remove();

  switch (returnOrder) {
    case "0":
      // Sort by name
      result.sort((a,b) => {
        if (a.productName.substring(0, 1).toLowerCase() < b.productName.substring(0, 1).toLowerCase()) return -1; 
        else return 1;
      });
      break;
    case "1":
      // Price
      result.sort((a,b) => {
        if (a.productPrice < b.productPrice) return -1; 
        else return 1;
      });
      break;
    default:
      // Eco factor
      result.sort((a,b) => {
        if (a.productEco < b.productEco) return -1; 
        else return 1;
      });
      break;
  }

  let index = 0;  // For pretty animations

  for (let queryItem of result) {
    // Iterate through and make the result cards
    index += 1;
    let newCard = document.createElement("div");
    newCard.className = "row mt-5 search-result justify-content-center";

    newCard.innerHTML = `
      <div class="col-8" data-aos="fade-up" data-aos-delay="${200 * index}" data-aos-anchor="#searchContainer">
        <div class="card">
            <div class="row">
                <div class="col-md-4">
                    <img src="/static/product/${queryItem.productId}.jpg" alt="Picture of ${queryItem.productName}" class="rounded-start img-fluid">
                </div>
                <div class="col-md-6">
                    <h5 class="card-title mt-md-2">${queryItem.productName}</h5>
                    <p class="card-text"><strong>£${queryItem.productPrice.toFixed(2)}</strong></p>
                    <p class="card-text text-muted">🍀Environmental score: ${queryItem.productEco}</p>
                </div>
                <div class="col-md-2 align-self-center">
                    <a class="btn btn-outline-primary btn-sm" href="/product/${queryItem.productId}">View</a>
                </div>
            </div>
        </div>
      </div>
    `;

    domElement.appendChild(newCard);
  }
}

function searchQuery() {
  // searchQuery() makes a search query to the server and then sends the result to be rendered

  // Get query params
  let query = {query: document.getElementById("search").value != "" ? document.getElementById("search").value : "ALL"};

  makeAPICall("QueryItems", query)
    .then((result) => {
      formatQueryResult(result);
    })
    .catch((err) => {
      console.log("API did not respond. Error " + err);
    });
}