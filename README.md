Currency exchange API
=======

REST API service for currency exchange calculator

# Setup
1. Clone the repository and prepare a virtual environment.
2. Install all dependencies from `requirements.txt`.
3. Apply all migrations, use the command
    ```bash
    python manage.py migrate
    ```
4. To load demo data into the database, use the command:
    ```bash
    python manage.py upload_csv exchange.csv
    ```
5. To start the service, use the command: 
    ```bash
   python manage.py runserver
   ```
6. You can find the rest of the information [here](http://127.0.0.1:8000/api/docs/) after you start the server.


# Some Solutions
* **Pandas** is used to load and format the data file.
* To obtain the price of a pair of currencies that does not have a direct exchange rate, we use the solution through **graphs**.
* Maybe the `endpoints exchange/`, `exchange/history` and `exchange/rate` should be merged into one, or maybe not, who knows. 
* The endpoints didn't turn out very pretty in their urls, I highly recommend using **swagger** to test the functionality.