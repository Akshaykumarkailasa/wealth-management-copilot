def get_portfolio(risk_type):

    if risk_type == "Conservative":

        return {
            "Stocks": 20,
            "Mutual Funds": 20,
            "Bonds": 40,
            "Gold": 20
        }

    elif risk_type == "Moderate":

        return {
            "Stocks": 50,
            "Mutual Funds": 25,
            "Bonds": 15,
            "Gold": 10
        }

    else:

        return {
            "Stocks": 70,
            "Mutual Funds": 15,
            "Bonds": 5,
            "Gold": 10
        }