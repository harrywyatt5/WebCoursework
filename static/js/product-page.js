'use strict';
"File name: main.js";
"Student Number: 22033329";

let optionsSelected = [];

function updateSelected() {
    // Might not be the most efficient way but the change event works very weirdly on inputs
    optionsSelected = [];
    let totalPrice = 0.0;

    // Iterate through all buttons. If they are selected, then add their value to the total price
    for (let button of document.querySelectorAll(".btn-check")) {
        if (button.checked === true) {
            optionsSelected.push(button.getAttribute("data-optionid"));
            totalPrice += parseFloat(button.value);
        }
    }

    let priceElement = document.getElementById("productPrice");
    priceElement.innerHTML = `<strong>£${(parseFloat(priceElement.getAttribute("data-baseprice")) + totalPrice).toFixed(2)}</strong>`;
}

function registerButtons() {
    // Find all the checkboxes/radios on the page and make sure they are accounted for when selected
    let buttons = document.querySelectorAll(".btn-check");

    for (let button of buttons) {
        addEventListener('change', updateSelected);
    }
}

function productAddToBasket(id) {
    // The add to basket function but under the context of being on the product page
    addToBasket(id, optionsSelected);
}