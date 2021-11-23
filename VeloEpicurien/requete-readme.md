# Voici les appels possibles pour l'application Vélo Épicurien

* ### @GET /readme

    * Retour: 
        - un fichier readme (en markdown) avec tous les appels possibles, les payloads attendus et la réponse de l'application.

* ### @GET /heartbeat
    * Payload : Aucun.
    * Retour:
        - villeChoisie: le nom de la ville choisie pour votre projet.   
  ```
  {
      "villeChoisie": str
  }
  ```
* ### @GET /extracted_data
    * Payload : Aucun.
    * Retour:
        - nbRestaurants: le nombre de restaurants nbRestaurants contenu dans votre base de données
        - nbSegments: le nombre de segments nbSegments dans votre base de données 
```
  {
      "nbRestaurants":int,
      "nbSegments":int
  }
```

  
* ### @GET /transformed_data
    * Payload : Aucun.
    * Retour:
        - restaurants: contient le nombre de restaurant par type dans votre BD de points de restaurants transformés
        - longueurCyclable : la valeur numérique qui contient la longueur totale des chemins pouvant être utilisés dans votre application
```
  {
      "restaurants":{
          $type1: int,
          $type2: int,
          ...
      },
      "longueurCyclable":float
  }
```
* ### @GET /type
    * Payload : Aucun.
    * Retour:
        - liste des types de restaurants disponibles dans la base de données
```
  [
      str,
      str,
      str,
      ...
  ]
```
* ### @GET /starting_point
    * Payload : 
        - length: longueur du trajet
        - type: liste des types de restaurants désirés
```
  {
    "length": int (en mètre),
    "type": [str, str, ... ]
  }
```

   * Retour:
      - startingPoint: objet géographique de type GeoPoint représentant un point de départ aléatoire
    
```
 {
    "startingPoint" : {"type":"Point", "coordinates":[float, float]}
 }
```

* ### @GET /parcours
    * Payload : 
        - startingPoint: objet GeoPoint représentant le point de départ
        - length: longueur du trajet
        - numberOfStops: nombre d'arrêt maximal du trajet
        - type: liste des types de restaurants désirés
```
  {
    "startingPoint" : {"type":"Point", "coordinates":[float, float]},
    "length": int (en mètre),
    "numberOfStops": int,
    "type": [str, str, ... ]
  }
```
   * Retour:
      - featureCollection: objet GeoJson représentant le trajet obtenu
      - features: soit un Point, représentant des restaurants, avec les propriétés name et type représentant respectivement le nom et le type du restaurant, soit un MultiLineString, représentant les segments cyclables, avec la propriété lenght représentant la longueur du segment
    
```
  {
    "type": "FeatureCollection",
    "features": [
        {
            "type":"Feature",
            "geometry":{
                "type": "Point",
                "coordinates":  [float, float]
            },
            "properties":{
                "name":str,
                "type":str
            }
        }, ..., {
            "type":"Feature",
            "geometry":{
                "type": "MultiLineString",
                "coordinates": [[
                     [float, float],  [float, float],  [float, float], ...
                    ]]
            },
            "properties":{
                "length":float (en mètres)
            }
        }
    ]
  }
```

