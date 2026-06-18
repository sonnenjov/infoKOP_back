from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Vest, Tag
from .serializers import VestSerializer, TagSerializer
from django.shortcuts import get_object_or_404
from .permissions import isReporterOrAdmin
import cloudinary.uploader
from django.utils import timezone
from django.db.models import F
import json


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_tags(request):
    tags = Tag.objects.all().order_by('name')
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tag(request):
    serializer = TagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_news(request):
    user = request.user
    if user.is_authenticated and hasattr(user, 'role') and user.role in ['reporter', 'admin']:
        news = Vest.objects.all().order_by('-created_at')
    else:
        news = Vest.objects.filter(status='objavljeno', is_visible=True).order_by('-created_at')
    serializer = VestSerializer(news, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([isReporterOrAdmin])
@parser_classes([MultiPartParser, FormParser])
def get_one_article_edit(request, id):
    try:
        article = Vest.objects.get(id=id)
    except Vest.DoesNotExist:
        return Response({'error': 'Vest nije pronađena'}, status=404)

    if request.method == 'GET':
        serializer = VestSerializer(article)
        return Response(serializer.data)

    elif request.method in ['PATCH', 'PUT']:
        data = request.data.copy()

        if 'image' in request.FILES:
            try:
                uploaded_image = cloudinary.uploader.upload(
                    request.FILES['image'],
                    folder='infokop/news'
                )
                data['image_url'] = uploaded_image['secure_url']
            except Exception as e:
                return Response({'error': f'Image upload failed: {str(e)}'}, status=400)

        if 'image' in data:
            del data['image']

        if 'tags' in data and isinstance(data['tags'], str):
            try:
                tags = json.loads(data['tags'])
                data.setlist('tag_ids', [str(tag) for tag in tags])
                del data['tags']
            except Exception:
                pass

        serializer = VestSerializer(article, data=data, partial=True)
        if serializer.is_valid():
            article = serializer.save()
            if request.data.get('status') == 'objavljeno' and article.status != 'objavljeno':
                article.published_at = timezone.now()
                article.save()
            return Response(VestSerializer(article).data)

        print(serializer.errors)
        return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_one_article_user(request, id):
    try:
        article = Vest.objects.get(id=id, status='objavljeno', is_visible=True)
    except Vest.DoesNotExist:
        return Response({'error': 'Vest nije pronadjena'}, status=404)

    Vest.objects.filter(id=id).update(views_count=F('views_count') + 1)
    article.refresh_from_db()
    serializer = VestSerializer(article)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([isReporterOrAdmin])
@parser_classes([MultiPartParser, FormParser])
def create_news(request):
    data = request.data.copy()
    cloudinary_url = None

    if 'image' in request.FILES:
        try:
            uploaded_image = cloudinary.uploader.upload(
                request.FILES['image'],
                folder='infokop/news'
            )
            cloudinary_url = uploaded_image['secure_url']
        except Exception as e:
            return Response({'error': f'Image upload failed: {str(e)}'}, status=400)

    if 'image' in data:
        del data['image']

    if cloudinary_url:
        data['image_url'] = cloudinary_url

    if 'tags' in data and isinstance(data['tags'], str):
        try:
            data['tags'] = json.loads(data['tags'])
        except Exception:
            pass

    serializer = VestSerializer(data=data)
    if serializer.is_valid():
        if serializer.validated_data.get('status') == 'objavljeno':
            serializer.save(author=request.user, published_at=timezone.now())
        else:
            serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    print(f"Serializer errors: {serializer.errors}")
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([isReporterOrAdmin])
def delete_news(request, id):
    article = get_object_or_404(Vest, id=id)

    if article.image:
        try:
            public_id = article.image.public_id
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")

    article.delete()
    return Response({"message": "Article and asset deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([isReporterOrAdmin])
@parser_classes([MultiPartParser, FormParser])
def update_news(request, id):
    try:
        article = Vest.objects.get(id=id)
    except Vest.DoesNotExist:
        return Response({'error': 'Vest nije pronađena'}, status=404)

    data = request.data.copy()

    if 'image' in request.FILES:
        try:
            if article.image:
                try:
                    public_id = article.image.public_id
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Error deleting old image: {e}")

            uploaded_image = cloudinary.uploader.upload(
                request.FILES['image'],
                folder='infokop/news'
            )
            data['image_url'] = uploaded_image['secure_url']
        except Exception as e:
            return Response({'error': f'Image upload failed: {str(e)}'}, status=400)

    if 'image' in data:
        del data['image']

    serializer = VestSerializer(article, data=data, partial=True)
    if serializer.is_valid():
        if request.data.get('status') == 'objavljeno' and article.status != 'objavljeno':
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()
        return Response(serializer.data, status=200)

    print(f"Serializer errors: {serializer.errors}")
    return Response(serializer.errors, status=400)