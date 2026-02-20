from django.db import models

class FacebookComment(models.Model):
    post_id = models.CharField(max_length=100, db_index=True)
    media_url = models.TextField(default='')  # Changé en TextField avec valeur par défaut vide
    comment_id = models.CharField(max_length=100, db_index=True)
    commenter_id = models.CharField(max_length=100, db_index=True)  # 👈 Nouveau champ ajouté
    comment_text = models.TextField()
    comment_likes = models.IntegerField(default=0)
    post_likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post_id', 'comment_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment {self.comment_id} by {self.commenter_id} on post {self.post_id}"



class YoutubeComment(models.Model):
    # Informations sur la vidéo
    video_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    views = models.IntegerField()
    likes_video = models.IntegerField()
    comment_text = models.TextField()  # Informations sur les commentaires
    created_at = models.DateTimeField(auto_now_add=True)  # Pour garder une trace de la date de création

    def __str__(self):
        return f"Commentaire de {self.comment_text[:50]}... sur {self.title} (ID: {self.video_id})"



class TwitterComment(models.Model):
    tweet_id = models.CharField(max_length=100)
    text = models.TextField()
    author_id = models.CharField(max_length=100)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.tweet_id} - {self.text[:30]}"
    
    class Meta:
        # Ajouter un index sur tweet_id pour des recherches plus rapides
        indexes = [
            models.Index(fields=['tweet_id']),
        ]
    
class poste(models.Model):
    id_poste = models.AutoField(primary_key=True)
    nom= models.CharField(max_length=50)
    contenue = models.CharField(max_length=2000)
    nombre_jaime = models.IntegerField(default=0)
    nombre_commentaire = models.IntegerField(default=0)
    nombre_republication = models.IntegerField(default=0)

class comments(models.Model):
    id_commentaire = models.AutoField(primary_key=True)
    nom= models.CharField(max_length=50)
    texte = models.CharField(max_length=2000)
    id_poste = models.ForeignKey(poste, on_delete=models.CASCADE)

# Ajoutez ce modèle si vous n'avez pas déjà un modèle pour les posts Facebook

    
   
    def __str__(self):
        return f"Post {self.id}: {self.message[:50]}..."
