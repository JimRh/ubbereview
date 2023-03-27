# TheBrain
BBE's Brain

Master: [![Build Status](https://travis-ci.com/BBEexpediting/TheBrain.svg?token=igAtPdK2ccmHYafa1imJ&branch=master)](https://travis-ci.com/BBEexpediting/TheBrain) 

Development [![Build Status](https://travis-ci.com/BBEexpediting/TheBrain.svg?token=igAtPdK2ccmHYafa1imJ&branch=development)](https://travis-ci.com/BBEexpediting/TheBrain)

## Carrier List
- FedEx
    - FedEx Express
    - FedEx Ground
-  Purolator
    - *Note: Purolator has been removed to improve system performance*
- DHL International
- UPS
    - *Note: UPS has been removed due to account incompatibilities*
- Canadian North
    - General
    - Guaranteed
    - Envelope
    - SCR Food
- Manitoulin
- Landtran Express
- TST
    - Maximum pickup date the same day as request, one month in future
    - Pickup start time between 8AM and 6PM
    - Pickup end time between 12 noon and 8PM
    - Pickup requires two hour minimum window
- Day & Ross
- Canadian Freightways
    - Maximum pickup date the same day as request, one month in future
    - Pickup start time between 8AM and 6PM
    - Pickup end time between 12 noon and 8PM
- Van Kam Freightways
    - Maximum pickup day the end of the current month
- Action Express
- WestJet
    - *Note: WestJet implementation is incomplete and will be available in the future*
- Overland West
- Comox Pacific
- ubbe ML
  - Machine learning and Google Distance Matrix API based rate
  - Only returned if no other carriers are returned
  
## Windows Installation
- configparser
  - pip install configparser
  - get a list of env variables and save as a structured .ini file
  - https://docs.python.org/3/library/configparser.html