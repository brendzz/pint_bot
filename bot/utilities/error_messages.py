"""A mapping of error codes to user friendly error messages and titles."""
ERROR_MESSAGES = {
    "CANNOT_OWE_SELF": {
        "title": "Cannot Owe Yourself",
        "description": "You can't owe yourself {CURRENCY_PLURAL}, that would be too confusing sorry. The {CURRENCY} economy is a complex system, and we don't want to break it."
     },
    "CANNOT_OWE_BOT": {
        "title": "Cannot Owe Bot",
        "description": "You can't owe a bot {CURRENCY_PLURAL}. That's just not how the {CURRENCY} economy works. Bots are here to help you free of charge."
    },
    "CANNOT_SETTLE_SELF": {
        "title": "Illegal {CURRENCY} Activities Detected",
        "description": "You can't have {CURRENCY} debts with yourself. You have the power to buy yourself a {CURRENCY} without the need for this bot."
     },
    "CANNOT_SETTLE_BOT": {
        "title": "Cannot Owe Bot",
        "description": "Due to {CURRENCY} Economy Financial Regulations, it is illegal to settle {CURRENCY_PLURAL} with {BOT_NAME} as it would be conflict of interest for {BOT_NAME} to run the {CURRENCY} economy and also participate in it."
    },
    "NEGATIVE_AMOUNT": {
        "title": "Negative Amount Detected",
        "description": "Negative {CURRENCY_PLURAL} detected! That's ILLEGAL!"
    },
    "ZERO_AMOUNT": {
        "title": "Zero Amount Detected",
        "description": "Zero {CURRENCY_PLURAL}? Really? Let's keep this to real debts."
    },
    "EXCEEDS_MAXIMUM": {
        "title": "Amount Too High",
        "description": "Do you really need to add that many {CURRENCY_PLURAL} at once? The maximum per debt is {MAX_DEBT}."
    },
    "VALIDATION_ERROR": {
        "title": "{BOT_NAME} Doesn't Like Your Data",
        "description": "Looks like you've got some invalid data there buddy - we've got rules around these parts."
    },
    "NOT_QUANTIZED": {
        "title": "Invalid Fraction",
        "description": "Woah there buckaroo, around these parts the {CURRENCY} amount must be a valid fraction and quantised to {SMALLEST_UNIT} {CURRENCY_PLURAL}."
    },
    "UNKNOWN_ERROR": {
        "title": "Unknown Error",
        "description": "An unknown error occurred. Please try again later."
    },
    "UNKNOWN_API_ERROR_FORMAT": {
        "title": "Unknown API Error Format",
        "description": "Unexpected error format received from the API."
    },
    "ERROR_PARSING_ERROR": {
        "title": "Error Parsing API Error",
        "description": "An error occurred while parsing the error message from the API."
    },
    "NO_DEBTS_FOUND": {
        "title": "No Debts Found",
        "description": "You don't owe that person any debts. The {CURRENCY} economy cannot function without debts! Please get some debts to avoid a financial collapse!"
    },
    "NO_DEBTS_IN_ECONOMY": {
        "title": "No {CURRENCY} Debts Found",
        "description": "The {CURRENCY} economy has no debts! It's the end!"
    },
    "INVALID_AMOUNT": {
        "title": "Invalid Amount",
        "description": "The amount you entered is invalid. Please enter a valid number."
    },
    "INVALID_TRANSACTION_TYPE": {
        "title": "Invalid Transaction Type",
        "description": "That is not a valid transaction type. Valid types are: owe, settle, cashout."
    },
    "INVALID_DATE": {
        "title": "Invalid Date",
        "description": "One of the dates you entered could not be understood. Please use a date like 25-12-2025."
    },
    "INVALID_API_KEY": {
        "title": "Not Authorised",
        "description": "The bot is not authorised to talk to the API. Please check the API_KEY configuration."
    },
    "DATA_STORE_UNAVAILABLE": {
        "title": "Economy on Fire",
        "description": "The economy data store is unavailable right now. Please try again later."
    },
    "REQUEST_ERROR": {
        "title": "Request Error",
        "description": "There was an error processing your request. Please try again later."
    }
}
