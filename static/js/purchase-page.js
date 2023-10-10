'use strict';
"File name: main.js";
"Student Number: 22033329";

const validators = {
    card_number: {regex: /^[0-9]{16}$/, message: "Card number must be 16 digits long"},
    cvc: {regex: /^[0-9]{3}$/, message: "CVC must be 3 digits long"},
    name: {regex: /^[a-zA-Z\s]{3,26}$/, message: "Name must be 3-26 Latin characters"},
    address_1: {regex: /^[0-9A-Za-z\s]{3,32}$/, message: "Name must be 3-26 Latin characters"},
    address_2: {regex: /^[0-9A-Za-z\s]{3,32}$/, message: "Name must be 3-26 Latin characters"},
    county: {regex: /^[a-zA-Z]{3,12}$/, message: "County must be 3-12 Latin characters"},
    postcode: {regex: /^[a-zA-Z]{1,2}[0-9]{1,2}[a-zA-Z]?\s[0-9][a-zA-Z]{2}$/, message: "Postcode is invalid"}
}

function onStartup() {
    // Get the modal
    let modal_element = document.getElementById("purchaseDialog");
    let modal = new bootstrap.Modal(modal_element, {
        backdrop: "static",
        keyboard: false
    });
    
    // If the user tries to quit out of the modal, go to the homepage
    modal_element.addEventListener('hide.bs.modal', () => {
        window.location.href = "/";
    });

    // Register the CVC button
    document.getElementById("cvcHint").addEventListener('click', cvcHint);

    modal.show();

    let inputs = document.querySelectorAll('.form-control');
    for (let inputElement of inputs) {
        inputElement.addEventListener('input', processFieldUpdate);
    }
}

function checkAllValid() {
    // Iterate through all the card form fields, check if they are valid
    let button = document.getElementById("submit");

    // Ensure it's disable to begin
    button.disabled = true;

    let inputs = document.querySelectorAll('.form-control');

    for (let inputElement of inputs) {
        // Check no fields are invalid
        if (inputElement.classList.contains("is-invalid")) return;

        // Check if all required fields are valid 
        if (inputElement.required === true) {
            if (!inputElement.classList.contains("is-valid")) return;
        }
    }

    // if we didn't return, allow the submit button
    button.disabled = false;
}

function toggleTooltip(element, isValid, message="") {
    // Toggle a tooltip on a field (or disable if the field is now correct)
    let tooltip = bootstrap.Tooltip.getInstance(element);

    if (isValid === true && tooltip != null) {
        // Destroy the tooltip
        tooltip.dispose();
    } else if (isValid === false && tooltip === null) {
        let newTooltip = new bootstrap.Tooltip(element, {
            title: message,
            trigger: 'manual',
            placement: 'auto'
        });

        newTooltip.show();
    } 
}

function toggleValidation(element, isValid) {
    // Checks the is-valid/is-invalid tag has been applied to fields

    // I'm really sorry
    if (element.classList.contains(isValid ? "is-invalid" : "is-valid")) element.classList.remove(isValid ? "is-invalid" : "is-valid");
    if (!element.classList.contains(isValid ? "is-valid" : "is-invalid")) element.classList.add(isValid ? "is-valid": "is-invalid");

    // Check if all values are valid
    checkAllValid();
}

function processFieldUpdate(event) {
    // When an input updates, check the new value is valid using regex or just comparing to the time w/ expiry 
    if (event.target.tagName != "SELECT") {
        let validator = validators[event.target.id];
        let isValid = validator.regex.test(event.target.value);

        toggleTooltip(event.target, isValid, validator.message);
        toggleValidation(event.target, isValid);
    } else {
        let date = new Date();

        let expiry = [document.getElementById("expiry_year"), document.getElementById("expiry_month")];
        let expiryYear = parseInt(expiry[0].value);
        let expiryMonth = parseInt(expiry[1].value);

        let isValid = expiryYear > date.getFullYear() || expiryYear === date.getFullYear() && expiryMonth >= date.getMonth();
        
        for (let expiryElement of expiry) {
            toggleTooltip(expiryElement, isValid, "Date must be in future");
            toggleValidation(expiryElement, isValid);
        }
    }
}

function cvcHint() {
    // Enable (or disable) the CVC hints
    let button = document.getElementById("cvcHint");
    let buttonTooltip = bootstrap.Tooltip.getInstance(button);

    if (buttonTooltip === null) {
        buttonTooltip = new bootstrap.Tooltip(button, {
            title: '<img class="img-fluid" src="static/img/card_cvc.png"><br>The CVC can be found on the back of your card',
            trigger: 'manual',
            html: true,
            placement: 'right'
        });

        buttonTooltip.show();
    } else {
        buttonTooltip.dispose();
    }
}

window.addEventListener('load', onStartup);