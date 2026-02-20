from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .forms import EmployeeLoginForm, EmployeeCreationForm
from .models import Employee, CustomUser
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from datetime import datetime

from django.views.decorators.csrf import csrf_protect
from django.utils import dateparse

# Ajoutez cette fonction d'aide quelque part dans votre fichier
def safe_parse_datetime(value):
    """Parse une date en gérant les erreurs de type."""
    if not isinstance(value, str):
        try:
            value = str(value)
        except:
            return None
    
    try:
        return dateparse.parse_datetime(value)
    except (TypeError, ValueError) as e:
        print(f"Erreur lors du parsing de la date: {e}, valeur: {value}")
        return None

# Ajoutez cette fonction pour déboguer
def debug_dateparse():
    import inspect
    import logging
    
    # Configuration du logging
    logging.basicConfig(filename='dateparse_debug.log', level=logging.DEBUG)
    
    # Fonction originale
    original_parse_datetime = dateparse.parse_datetime
    
    # Fonction de remplacement avec logging
    def logged_parse_datetime(value):
        caller_frame = inspect.currentframe().f_back
        caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        logging.debug(f"parse_datetime appelé depuis {caller_info} avec value={value} (type={type(value)})")
        
        if not isinstance(value, str):
            logging.error(f"TypeError: value n'est pas une chaîne mais {type(value)}")
            try:
                value = str(value)
                logging.debug(f"Conversion en chaîne réussie: {value}")
            except Exception as e:
                logging.error(f"Échec de la conversion en chaîne: {e}")
                return None
        
        try:
            result = original_parse_datetime(value)
            logging.debug(f"Résultat: {result}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du parsing: {e}")
            return None
    
    # Remplacer la fonction originale
    dateparse.parse_datetime = logged_parse_datetime
    logging.debug("Fonction parse_datetime remplacée par la version avec logging")

# Appelez cette fonction au démarrage de l'application
debug_dateparse()

from django.core.mail import send_mail
from django.conf import settings
 

from .models import DemoRequest
import json
from .predict import predict_comment  # importe ta fonction de traitement

from django.shortcuts import render
from scraping.facebook_scraper import scrape_facebook  # Importer ta fonction de scraping
from scraping.models import FacebookComment 

from django.http import HttpResponseRedirect
from scraping.models import YoutubeComment
from scraping.youtube_scraper import scrape_youtube_data

from scraping.models import TwitterComment
from scraping.twitter_scraper import fetch_and_store_tweets

from scraping.models import poste, comments
from django.shortcuts import redirect
# from scraping.linkdin_scraper import collecter
from django.http import HttpResponse
from scraping.linkdin_scraper import lancer_navigation_linkedin, extraire_et_enregistrer


# --- Connexion Employé ---
class EmployeeLoginView(LoginView):
    template_name = 'accounts/employee_login.html'
    authentication_form = EmployeeLoginForm

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return '/accounts/admin/dashboard/'
        elif hasattr(user, 'is_employee') and user.is_employee:
            return reverse_lazy('employee_dashboard')
        return '/'

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            if user.is_employee or user.is_superuser:
                login(self.request, user)
                return super().form_valid(form)
            else:
                form.add_error(None, "Ce compte n'a pas les permissions nécessaires.")
                return self.form_invalid(form)
        else:
            form.add_error(None, "Identifiants incorrects.")
            return self.form_invalid(form)

# --- Connexion Admin personnalisée ---
class AdminLoginView(LoginView):
    template_name = 'accounts/admin_login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return '/accounts/admin/dashboard/'
        else:
            messages.error(self.request, "Vous n'avez pas accès à cette section.")
            return '/accounts/admin/login/'

# --- Fonction pour vérifier superuser ---
def is_superuser(user):
    return user.is_authenticated and user.is_superuser



@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_employee(request, employee_id):
    try:
        employee = Employee.objects.select_related('user').get(id=employee_id)
        data = {
            'firstname': employee.firstname,
            'username': employee.user.username,
            'email': employee.user.email,
            'start_date': employee.start_date.strftime('%Y-%m-%d'),
            'address': employee.address
        }
        return JsonResponse(data)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employé non trouvé'}, status=404)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_employee(request, employee_id):
    if not request.method == 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        employee = Employee.objects.select_related('user').get(id=employee_id)
        
        # Récupération des données du formulaire
        data = request.POST
        print("Données reçues pour édition:", data)  # Debug
        
        # Mise à jour des données de l'employé
        employee.firstname = data.get('firstname', employee.firstname)
        
        # Conversion de la date
        start_date = data.get('start_date')
        if start_date:
            employee.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        employee.address = data.get('address', employee.address)
        
        # Mise à jour des données de l'utilisateur
        employee.user.username = data.get('username', employee.user.username)
        employee.user.email = data.get('email', employee.user.email)
        
        # Sauvegarder les modifications
        with transaction.atomic():
            employee.user.save()
            employee.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Employé modifié avec succès',
            'data': {
                'id': employee.id,
                'firstname': employee.firstname,
                'username': employee.user.username,
                'email': employee.user.email,
                'start_date': employee.start_date.strftime('%Y-%m-%d'),
                'address': employee.address
            }
        })
    
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employé non trouvé'}, status=404)
    except ValueError as e:
        print(f"Erreur de validation: {str(e)}")  # Debug
        return JsonResponse({'error': 'Format de date invalide'}, status=400)
    except Exception as e:
        print(f"Erreur lors de l'édition: {str(e)}")  # Debug
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_employee(request, employee_id):
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        user = employee.user
        
        with transaction.atomic():
            employee.delete()
            user.delete()
        
        messages.success(request, "Employé supprimé avec succès.")
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def employee_dashboard(request):
    # Récupérer l'employé connecté
    employee = get_object_or_404(Employee, user=request.user)
    
    # Déterminer l'onglet actif
    active_tab = request.POST.get('active_tab', 'facebook')
    
    # Traitement des données Facebook
    if request.method == "POST" and 'facebook_data' in request.POST:
        # Votre code existant pour Facebook
        pass
    
    # Traitement des données YouTube
    if request.method == "POST" and 'youtube_data' in request.POST:
        # Votre code existant pour YouTube
        pass
    
    # Récupérer les données LinkedIn
    linkedin_posts = poste.objects.all().order_by('-id_poste')
    
    # Récupérer les données Facebook
    facebook_data = FacebookComment.objects.all().order_by('-created_at')
    
    # Récupérer les données YouTube
    youtube_data = YoutubeComment.objects.all().order_by('-created_at')
    
    # Récupérer les données Twitter
    twitter_data = TwitterComment.objects.all().order_by('-created_at')
    
    # Combiner les données dans un seul contexte
    context = {
        'user': request.user,
        'facebook_data': facebook_data,
        'youtube_data': youtube_data,
        'twitter_data': twitter_data,
        'linkedin_data': linkedin_posts,
        'employee': employee,
        'active_tab': active_tab,  # Ajouter l'onglet actif au contexte
    }
    
    return render(request, 'accounts/employee_dashboard.html', context)

def landing_page(request):
    return render(request, 'accounts/landing_page.html')  # Chemin relatif au répertoire des templates

def custom_logout(request):
    logout(request)
    return redirect('landing_page')  # Chemin relatif au répertoire des templates

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_employee(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        with transaction.atomic():
            # Récupération des données
            data = request.POST
            
            # Vérification des champs requis
            required_fields = ['username', 'email', 'password', 'start_date', 'address']
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"Le champ {field} est requis")

            # Création de l'utilisateur
            user = CustomUser.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                is_employee=True,
                is_active=True
            )

            # Création de l'employé
            employee = Employee.objects.create(
                user=user,
                firstname=data['username'],
                start_date=data['start_date'],
                address=data['address']
            )

            return JsonResponse({
                'status': 'success',
                'employee_id': employee.id
            })

    except ValueError as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@csrf_exempt
def request_demo(request):
    if request.method == 'POST':
        try:
            # Récupération des données
            try:
                data = json.loads(request.body)
            except:
                data = request.POST
            
            # Validation des données
            required_fields = ['name', 'email', 'phone', 'role']
            if not all(field in data for field in required_fields):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tous les champs sont obligatoires'
                }, status=400)

            # Enregistrement dans la base de données
            DemoRequest.objects.create(
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                role=data['role'],
                company=data.get('company', '')  # Champ optionnel
            )
            
            # Envoi de l'e-mail de démo
            # Utilisez l'URL correcte qui correspond à votre configuration d'URL
            demo_url = 'http://127.0.0.1:8000/accounts/Demo/'  # Notez le slash à la fin
            user_email = data['email']

            send_mail(
                subject="Découvrez votre démo personnalisée",
                message=(
                    f"Bonjour {data['name']},\n\n"
                    f"Merci pour votre demande de démonstration.\n\n"
                    f"Voici votre lien d'accès à la démo interactive :\n{demo_url}\n\n"
                    "Cordialement,\nL'équipe SentiSort"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Votre demande a bien été enregistrée. Nous vous contacterons rapidement.'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f"Une erreur s'est produite: {str(e)}"
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Méthode non autorisée'
    }, status=405)  





@csrf_exempt
def predict_view(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            comment = data.get("comment")

            if not comment:
                return JsonResponse({"error": "Aucun commentaire reçu."}, status=400)

            # Version simplifiée pour tester
            result = {
                "commentaire": comment,
                "langue": "fr",
                "sentiment": {
                    "valeur": "Positif",
                    "confiance": "75.00%"
                },
                "categorie": {
                    "valeur": "Feedback positif",
                    "confiance": "80.00%"
                }
            }
            
            # Décommentez cette ligne une fois que vous avez vérifié que le reste fonctionne
            # result = predict_comment(comment)
            
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Format JSON invalide."}, status=400)
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Affiche la trace complète de l'erreur
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

def demo_page(request):
    # Utilisez le chemin complet du template
    return render(request, 'accounts/demo.html')


# # la fonction pour lancer le scraper LinkedIn
# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def launch_linkedin_scraper(request):
#     print("📝 Lancement du scraper LinkedIn")

#     if request.method == "POST":
#         try:
#             collecter_commentaires()
#             print("✅ Données récupérées avec succès !")
#         except Exception as e:
#             print(f"❌ Erreur lors de l'exécution du scraper : {str(e)}")
#             return HttpResponse(f"Erreur lors de l'exécution du scraper : {str(e)}", status=500)

#     return redirect('admin_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def etape1_linkedin(request):
    if request.method == "POST":
        print("Étape 1 : Lancement de la navigation LinkedIn")
        lancer_navigation_linkedin()
    
    # Rediriger vers la page d'origine avec l'onglet LinkedIn actif
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def etape2_linkedin(request):
    if request.method == "POST":
        print("Étape 2 : Extraction et enregistrement des données LinkedIn")
        extraire_et_enregistrer()
    
    # Rediriger vers la page d'origine avec l'onglet LinkedIn actif
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')


# Tous ce qui a relation avec l'admin
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    print(f"📩 Requête reçue : {request.method}")

    admin = request.user
    employees = Employee.objects.select_related('user').all()
    print(f"Nombre d'employés trouvés : {employees.count()}")
    
    # Déterminer l'onglet actif
    active_tab = request.POST.get('active_tab', request.GET.get('active_tab', 'facebook'))
    
    # Traitement des formulaires
    if request.method == "POST":
        # Traitement pour YouTube
        if 'youtube_data' in request.POST:
            try:
                print("Récupération des données YouTube...")
                from scraping.youtube_scraper import scrape_youtube_data
                results = scrape_youtube_data()
                messages.success(request, f"{len(results)} commentaires YouTube récupérés avec succès!")
            except Exception as e:
                print(f"Erreur lors de la récupération des données YouTube: {str(e)}")
                messages.error(request, f"Erreur: {str(e)}")
        
        # Traitement pour Facebook
        elif 'facebook_data' in request.POST:
            try:
                print("Récupération des données Facebook...")
                from scraping.facebook_scraper import scrape_facebook
                results = scrape_facebook()
                messages.success(request, f"{len(results)} commentaires Facebook récupérés avec succès!")
            except Exception as e:
                print(f"Erreur lors de la récupération des données Facebook: {str(e)}")
                messages.error(request, f"Erreur: {str(e)}")
        
        # Traitement pour Twitter
        elif 'twitter_data' in request.POST:
            try:
                print("Récupération des données Twitter...")
                from scraping.twitter_scraper import fetch_and_store_tweets
                tweets = fetch_and_store_tweets()
                
                # Vérifier si des tweets ont été créés
                if tweets:
                    messages.success(request, f"{len(tweets)} tweets disponibles dans la base de données!")
                else:
                    # Forcer la création de données de test si aucun tweet n'a été retourné
                    from scraping.twitter_scraper import create_test_data
                    test_tweets = create_test_data()
                    messages.warning(request, f"Impossible de récupérer des tweets réels. {len(test_tweets)} tweets de test ont été créés.")
            except Exception as e:
                print(f"Erreur lors de la récupération des données Twitter: {str(e)}")
                messages.error(request, f"Erreur: {str(e)}")
                # En cas d'erreur, essayer de créer des données de test
                try:
                    from scraping.twitter_scraper import create_test_data
                    test_tweets = create_test_data()
                    messages.warning(request, f"Erreur API, mais {len(test_tweets)} tweets de test ont été créés.")
                except Exception as inner_e:
                    messages.error(request, f"Impossible de créer des données de test: {str(inner_e)}")
    
    # 📥 Données à afficher
    facebook_data = FacebookComment.objects.all().order_by('-created_at')
    youtube_data = YoutubeComment.objects.all().order_by('-created_at')
    twitter_data = TwitterComment.objects.all().order_by('-created_at')
    linkedin_posts = poste.objects.all().order_by('-id_poste')
    
    # Ajouter des données de test pour Facebook si aucune donnée n'existe
    if not facebook_data.exists():
        print("Aucune donnée Facebook trouvée, ajout de données de test")
    
    # Statistiques Facebook
    facebook_stats = {
        'total_likes': facebook_data.count() * 10,
        'comments': facebook_data.count(),
        'reach': 1000,
        'shares': 500
    }
    
    print(f"Données Facebook: {facebook_data.count()} commentaires")
    print(f"Données YouTube: {youtube_data.count()} commentaires")
    print(f"Données Twitter: {twitter_data.count()} tweets")
    print(f"Données LinkedIn: {linkedin_posts.count()} posts")

    context = {
        'employees': employees,
        'facebook_data': facebook_data,
        'youtube_data': youtube_data,
        'twitter_data': twitter_data,
        'linkedin_data': linkedin_posts,
        'facebook_stats': facebook_stats,
        'admin': admin,
        'active_tab': active_tab,
    }

    return render(request, 'accounts/admin_dashboard.html', context)


# Afficher les données de Facebook et YouTube dans le employee_dashboard
@login_required
def employee_dashboard(request):
    
    # Récupérer l'employé connecté
    employee = get_object_or_404(Employee, user=request.user)

    # Récupérer les données LinkedIn
    linkedin_posts = poste.objects.all().order_by('-id_poste')

    # Récupérer les données Facebook
    facebook_data = FacebookComment.objects.all().order_by('-created_at')
    
    # Récupérer les données YouTube
    youtube_data = YoutubeComment.objects.all().order_by('-created_at')

    # Récupérer les données Twitter
    twitter_data = TwitterComment.objects.all().order_by('-created_at')

    # Combiner les données dans un seul contexte
    context = {
        'user': request.user,
        'facebook_data': facebook_data,
        'youtube_data': youtube_data,
        'twitter_data': twitter_data,
        'linkedin_data': linkedin_posts,
        'employee': employee,
    }
    
    return render(request, 'accounts/employee_dashboard.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        if email != user.email and CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé par un autre utilisateur.")
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('employee_dashboard')
        
        # Mettre à jour les informations
        user.username = username
        user.email = email
        user.save()
        
        messages.success(request, "Profil mis à jour avec succès.")
    
    # Rediriger vers le tableau de bord approprié
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')

@login_required
def update_profile_image(request):
    if request.method == 'POST' and request.FILES.get('profile_image'):
        user = request.user
        user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, "Photo de profil mise à jour avec succès.")
    
    # Rediriger vers le tableau de bord approprié en fonction du rôle de l'utilisateur
    if user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_facebook_post(request):
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            message = request.POST.get('message', '')
            link = request.POST.get('link', '')
            image = request.FILES.get('image')
            
            # Validation des données
            if not message:
                messages.error(request, "Le message ne peut pas être vide.")
                return redirect('admin_dashboard')
            
            # Créer un nouveau post Facebook dans la base de données
            post = FacebookPost(
                message=message,
                link=link,
                likes=0,
                comments=0,
                shares=0
            )
            
            # Enregistrer le post d'abord
            post.save()
            
            # Gérer l'image si elle existe
            if image:
                # Assurez-vous que MEDIA_URL et MEDIA_ROOT sont configurés dans settings.py
                from django.conf import settings
                import os
                from datetime import datetime
                
                # Créer un nom de fichier unique
                filename = f"facebook_post_{post.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{os.path.splitext(image.name)[1]}"
                
                # Chemin complet où l'image sera sauvegardée
                filepath = os.path.join(settings.MEDIA_ROOT, 'facebook_posts', filename)
                
                # Créer le dossier s'il n'existe pas
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Sauvegarder l'image
                with open(filepath, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                
                # Mettre à jour l'URL de l'image dans le post
                post.media_url = os.path.join(settings.MEDIA_URL, 'facebook_posts', filename)
                post.save()
            
            messages.success(request, "Post Facebook créé avec succès!")
            
            # Rediriger vers le dashboard avec l'onglet Facebook actif
            return redirect('admin_dashboard')
        
        except Exception as e:
            print(f"Erreur lors de la création du post: {str(e)}")
            messages.error(request, f"Erreur lors de la création du post: {str(e)}")
            return redirect('admin_dashboard')
    
    # Si la méthode n'est pas POST, rediriger vers le dashboard
    return redirect('admin_dashboard')
