import pandas as pd
import csv
import json

class CartProcessor:
    def __init__(self, df, csv_file):
        """
        Initialize the CartProcessor with the DataFrame and file path.
        
        Args:
        df (pd.DataFrame): The DataFrame containing cart and user data.
        csv_file (str): Path to the CSV file for updating data.
        """
        self.df = df
        self.csv_file = csv_file

    def pullcart(self, cartloc):
        """
        Retrieve cart data for a given cart location from the DataFrame.
        
        Args:
        cartloc (int): The cart number (1-based index).
        
        Returns:
        list: A structured list of items in the cart.
        """
        cart = self.df.iloc[cartloc - 1, 27]  # Assuming cart data is in the 28th column
        elements = [x.strip() for x in cart.split(",")]
        result = [[elements[i], int(elements[i + 1])] for i in range(0, len(elements), 2)]
        return result

    def pullrestock(self, coor):
        """
        Retrieve restock frequencies for products.
        
        Args:
        coor (list): List of coordinates for items.
        
        Returns:
        list: Restock frequencies for the products.
        """
        restock_frequencies = []
        for i in range(4):  # Assuming there are 4 items to process
            restock_frequency = self.df.iloc[i, 12]  # Assuming restock frequency is in the 13th column
            restock_frequencies.append(restock_frequency)
        return restock_frequencies

    def pullitem(self, cart):
        """
        Retrieve item coordinates and letters.
        
        Args:
        cart (list): List of items in the cart.
        
        Returns:
        tuple: Coordinates and item letters.
        """
        letters = [item[0] for item in cart]
        coor = []
        for letter in letters:
            result = [(i, j) for i in range(len(self.df)) for j in range(len(self.df.columns)) if self.df.iloc[i, j] == letter]
            if result:
                row, col = result[0]
                coor.append(row)
        return coor, letters

    def pullrating(self, coor):
        """
        Retrieve item rating properties.
        
        Args:
        coor (list): List of coordinates for items.
        
        Returns:
        list: Properties of the items.
        """
        itemsprop = []
        for i in coor:
            item_properties = [self.df.iloc[i, x + 12] for x in range(3)]  # Assuming ratings are in columns 13-15
            itemsprop.append(item_properties)
        return itemsprop

    def update_rating(self, coor, new_rating):
        """
        Update the rating data in the DataFrame and save it to the CSV file.
        
        Args:
        coor (list): List of coordinates for items.
        new_rating (list): New rating data for the items.
        """
        for i in range(len(coor)):
            for x in range(2):  # Assuming 2 columns need updating
                self.df.iloc[coor[i], x + 13] = new_rating[i][x + 1]
        self.df.to_csv(self.csv_file, index=False)
        print("Database has been updated.")

    def update_user_voucher(self, user_ID, user_voucher):
        """
        Update the user voucher in the CSV file.
        
        Args:
        user_ID (str): The user ID to update.
        user_voucher (str): The new voucher value.
        """
        data = []
        with open(self.csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['user_ID'] == user_ID:
                    row['user_voucher'] = user_voucher
                data.append(row)
        with open(self.csv_file, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print("User voucher updated.")

    def prepare_data_to_send(self):
        """
        Prepare the data payload for BLE communication.
        
        Returns:
        dict: The data payload ready to send via BLE.
        """
        cartloc = self.df['cart'][self.df['cart'].notna()].iloc[-1]
        cart = self.pullcart(cartloc)
        coor, letters = self.pullitem(cart)
        restock_frequencies = self.pullrestock(coor)
        item_properties = self.pullrating(coor)

        user_ID = self.df.iloc[cartloc - 1, 26]
        user_voucher_eligible = self.df.iloc[cartloc - 1, 7] == 'yes'

        cart_data = {}
        for i, product in enumerate(cart):
            rating_total = int(item_properties[i][0])
            rating_frequency = int(item_properties[i][1])
            cart_data[product[0]] = {
                "rating_total": rating_total,
                "rating_frequency": rating_frequency,
            }

        restock_frequency = {}
        letters = ['A', 'B', 'C', 'D']
        for x in range(len(restock_frequencies)):
            restock_frequency[letters[x]] = int(restock_frequencies[x])

        return {
            "user_ID": str(int(user_ID)),
            "user_voucherEligible": user_voucher_eligible,
            "cart": cart_data,
            "restock_frequency": restock_frequency
        }





class DatabaseProcessor:
    def __init__(self, file_path):
        """
        Initialize the DatabaseProcessor with the file path.
        
        Args:
        file_path (str): Path to the CSV file.
        """
        self.file_path = file_path

    def update_rating(self, coor, new_rating):
        """
        Update the ratings in the DataFrame and save to the CSV file.
        
        Args:
        coor (list): Coordinates of the items in the DataFrame.
        new_rating (list): New rating data to update.
        """
        df = pd.read_csv(self.file_path)
        for i in coor:
            for x in range(2):  # Assuming updating columns 13 and 14
                df.iloc[i, x + 13] = new_rating[i][x + 1]
        df.to_csv(self.file_path, index=False)
        print("Database has been updated.")

    def pull_product(self, cart):
        """
        Retrieve product coordinates from the DataFrame based on the cart data.
        
        Args:
        cart (list): List of cart items with their details.
        
        Returns:
        list: Row coordinates of the products in the DataFrame.
        """
        df = pd.read_csv(self.file_path)
        product = [item[0] for item in cart]
        product_id = [item.replace('Product ', '') for item in product]
        coor = []

        for pid in product_id:
            result = [(i, j) for i in range(len(df)) for j in range(len(df.columns)) if df.iloc[i, j] == pid]
            if result:
                row, col = result[0]
                coor.append(row)
        return coor

    async def run(self, json_data):
        """
        Process the JSON data to update the ratings and user voucher in the database.
        
        Args:
        json_data (str): JSON string containing user and cart data.
        """
        df = pd.read_csv(self.file_path)
        data = json.loads(json_data)

        # Extract user info
        user_info = [data["user_ID"], data["user_voucher"]]

        # Extract cart items
        cart_items = [
            [product, details["rating_total"], details["rating_frequency"]]
            for product, details in data["cart"].items()
        ]

        # Get product coordinates
        coor = self.pull_product(cart_items)
        print("Cart items:", cart_items)

        # Update ratings
        self.update_rating(coor, cart_items)

        # Update user voucher
        self.update_user_voucher(user_info[0], user_info[1])
        print("User voucher updated.")

    def update_user_voucher(self, user_ID, user_voucher):
        """
        Update the user's voucher in the CSV file.
        
        Args:
        user_ID (str): The user ID to update.
        user_voucher (str): The new voucher value.
        """
        data = []
        with open(self.file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['user_ID'] == user_ID:
                    row['user_voucher'] = user_voucher
                data.append(row)

        with open(self.file_path, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


# # Example Usage
# if __name__ == "__main__":
#     csv_file = "path/to/your/csvfile.csv"
#     df = pd.read_csv(csv_file)

#     # Initialize the processor
#     processor = CartProcessor(df, csv_file)

#     # Prepare data for BLE communication
#     data_to_send_ble = processor.prepare_data_to_send()
#     print("Data to send via BLE:", data_to_send_ble)
