import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class SentimentAnalyzer:
    def __init__(self, model_name='distilbert-base-uncased-finetuned-sst-2-english'):
        # Ініціалізація токенізатора
        # Токенізатор перетворює текст на числові токени
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Завантаження попередньо навченої моделі для класифікації
        # Модель навчена на Stanford Sentiment Treebank (SST-2)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def analyze_sentiment(self, text):
        # Токенізація тексту
        # return_tensors="pt" - повертає PyTorch тензори
        # truncation=True - обрізає довгі тексти
        # padding=True - додає паддінг для однакової довжини
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True
        )

        # Вимкнення обчислення градієнтів для inference
        with torch.no_grad():
            # Пропускання через модель
            outputs = self.model(**inputs)

        # Застосування softmax для перетворення логітів в ймовірності
        probabilities = torch.softmax(outputs.logits, dim=1)

        # Знаходження індексу максимальної ймовірності
        sentiment = torch.argmax(probabilities, dim=1)

        # Повернення результату
        return {
            'sentiment': 'Positive' if sentiment.item() == 1 else 'Negative',
            'confidence': probabilities.max().item(),
            'raw_probabilities': probabilities.numpy().tolist()
        }

# Демонстрація використання
def main():
    # Створення екземпляру аналізатора
    analyzer = SentimentAnalyzer()

    # Набір тестових текстів
    test_texts = [
        "This product is amazing!",
        "I'm really disappointed with the service.",
        "It was an okay experience.",
        "Absolutely terrible and waste of money!"
    ]

    # Аналіз кожного тексту
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"Текст: {text}")
        print(f"Тональність: {result['sentiment']}")
        print(f"Впевненість: {result['confidence']:.2%}")
        print(f"Деталізація ймовірностей: {result['raw_probabilities']}")
        print("-" * 50)

# Виклик основної функції
if __name__ == "__main__":
    main()