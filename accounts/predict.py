import numpy as np
# import fasttext
from tensorflow import keras

def detect_language(text):
    model_lang_detect = fasttext.load_model("lid.176.bin")
    prediction = model_lang_detect.predict(text)
    label = prediction[0][0]  # ex : __label__fr
    lang = label.replace("__label__", "")
    del model_lang_detect
    return lang

def sentence_to_vector(sentence, ft_model, max_len=100):
    words = sentence.split()
    vectors = [ft_model.get_word_vector(word) for word in words]

    if len(vectors) > max_len:
        vectors = vectors[:max_len]
    elif len(vectors) < max_len:
        padding = [np.zeros(300)] * (max_len - len(vectors))
        vectors.extend(padding)

    return np.array(vectors)

def predict_comment(text):
    language = detect_language(text)
    print(f"Langue détectée : {language}")

    if language == "fr":
        sentiment_model_path = "best_sentimentCNN_model.keras"
        fasttext_model_path = "cc.fr.300.bin"
    elif language == "en":
        sentiment_model_path = "bestEN_sentiment_modelBILSTM.keras"
        fasttext_model_path = "cc.en.300.bin"
    else:  # arabe
        sentiment_model_path = "Meilleur_sentiment_model_arabic.keras"
        fasttext_model_path = "cc.ar.300.bin"

    # Charger FastText
    print("Chargement FastText...")
    ft = fasttext.load_model(fasttext_model_path)

    # Encoder texte
    vectorized_text = np.expand_dims(sentence_to_vector(text, ft), axis=0)
    print("Shape de vectorized_text:", vectorized_text.shape)

    del ft

    # Charger modèle de sentiment
    print("Chargement modèle sentiment...")
    sentiment_model = keras.models.load_model(sentiment_model_path)
    print("Modèle sentiment chargé ✅")

    # Prédire le sentiment
    sentiment_pred = sentiment_model.predict(vectorized_text)[0][0]
    sentiment = "Positif" if sentiment_pred >= 0.5 else "Negatif"
    sentiment_confidence = sentiment_pred * 100 if sentiment_pred >= 0.5 else (1 - sentiment_pred) * 100

    del sentiment_model

    print(f"Sentiment prédit: {sentiment} ({sentiment_confidence:.2f}%)")

    # Choisir modèle de catégorie
    if language == "fr":
        if sentiment == "Positif":
            category_model_path = "positive_categories.keras"
            categories = ["Feedback positif", "Information", "Prix", "Livraison", "Service Client"]
        else:
            category_model_path = "negative_categories.keras"
            categories = ["Feedback négatif", "Prix", "Service Client", "Livraison", "Vulgarité"]
    elif language == "en":
        if sentiment == "Positif":
            category_model_path = "EN_positive_category_modelBILSTM.keras"
            categories = ["Positive Feedback", "Information", "Price", "Delivery", "Customer Service"]
        else:
            category_model_path = "EN_negative_category_modelBILSTM.keras"
            categories = ["Negative Feedback", "Price", "Customer Service", "vulgarity", "spam" , "delivery"]
    else:  # arabe
        if sentiment == "Positif":
            category_model_path = "positive_category_model_arabic.keras"
            categories = ["مراجعة إيجابية", "معلومة", "السعر", "التوصيل", "خدمة العملاء"]
        else:
            category_model_path = "negative_category_model_arabic.keras"
            categories = ["مراجعة سلبية", "السعر", "كلام فاحش", "خدمة العملاء", "spam", "التوصيل"]

    print("Chargement modèle catégorie...")
    category_model = keras.models.load_model(category_model_path)
    print("Modèle catégorie chargé ✅")

    # Prédire catégorie
    category_pred = category_model.predict(vectorized_text)[0]
    category_index = np.argmax(category_pred)
    category_confidence = np.max(category_pred) * 100
    predicted_category = categories[category_index]

    del category_model

    # Retourner résultat
    result = {
        "commentaire": text,
        "langue": language,
        "sentiment": {
            "valeur": sentiment,
            "confiance": f"{sentiment_confidence:.2f}%"
        },
        "categorie": {
            "valeur": predicted_category,
            "confiance": f"{category_confidence:.2f}%"
        }
    }

    return result