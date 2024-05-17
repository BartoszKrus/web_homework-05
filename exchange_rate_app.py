import asyncio
import aiohttp
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


API_URL = "https://api.nbp.pl/api/exchangerates/tables/a/"
TODAY = datetime.today().strftime("%Y-%m-%d")


class ExchangeRateProvider(ABC):
    @abstractmethod
    async def get_rates(self, date):
        pass


class NBPRateProvider(ExchangeRateProvider):
    async def get_rates(self, date):
        url = f"{API_URL}{date}?format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    raise RuntimeError(f"Data download error: {response.status}")


class BasicRateDisplayer:
    def display_basic_currencies(self, results):
        if not results:
            print("No data available.")
            return

        for i, result in enumerate(results, 1):
            date_to_print = (datetime.strptime(TODAY, '%Y-%m-%d') - timedelta(days=i - 1)).date()
            print(f"Data as of day {date_to_print}:")
            if result and result != []:
                for currency in result[0]["rates"]:
                    if currency['code'] in ('EUR', 'USD'):
                        print(f"{currency['currency']:36} {currency['code']:4} {currency['mid']}")
            else:
                print("No data.")
            print()


class AdditionalRateDisplayer:
    def display_additional_currencies(self, available_currencies_set, results):
        if not available_currencies_set:
            print("No additional currencies available.")
            return

        currency_choice = input(
            f"Enter the currency abbreviation (available: {', '.join(available_currencies_set)}): ").upper()
        if currency_choice in available_currencies_set:
            for i, result in enumerate(results, 1):
                date_to_print = (datetime.strptime(TODAY, '%Y-%m-%d') - timedelta(days=i - 1)).date()
                print(f"Data as of day {date_to_print}:")
                if result and result != []:
                    for currency in result[0]["rates"]:
                        if currency['code'] == currency_choice:
                            print(f"{currency['currency']:36} {currency['code']:4} {currency['mid']}")
                            break
                else:
                    print("No data.")
                print()
        else:
            print("There is no such currency on the list.")


class UserInteraction:
    def __init__(self, basic_rate_displayer, additional_rate_displayer):
        self.basic_rate_displayer = basic_rate_displayer
        self.additional_rate_displayer = additional_rate_displayer

    async def main(self, days):
        """The function retrieves exchange rates for several days."""
        rate_provider = NBPRateProvider()
        tasks = [rate_provider.get_rates((datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=i)).strftime("%Y-%m-%d"))
                 for i in range(days)]
        results = await asyncio.gather(*tasks)

        self.basic_rate_displayer.display_basic_currencies(results)

        additional_currencies = set()
        for result in results:
            if result and result != []:
                additional_currencies.update(
                    currency['code'] for currency in result[0]["rates"] if currency['code'] not in ('EUR', 'USD'))

        while True:
            choice = input("Do you want to see rates for other currencies? (Y/N):")
            if choice.upper() == 'Y':
                self.additional_rate_displayer.display_additional_currencies(additional_currencies, results)
            elif choice.upper() == 'N':
                break
            else:
                print("Incorrect selection, select 'Y' or 'N'.")


if __name__ == "__main__":
    try:
        days = int(input("Enter the number of days (maximum 10):"))
        if days > 10:
            raise ValueError("The number of days cannot be more than 10")
    except ValueError as e:
        print(f"Error: {e}")
    else:
        basic_rate_displayer = BasicRateDisplayer()
        additional_rate_displayer = AdditionalRateDisplayer()
        user_interaction = UserInteraction(basic_rate_displayer, additional_rate_displayer)
        asyncio.run(user_interaction.main(days))
