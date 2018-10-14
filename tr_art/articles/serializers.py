import datetime

from django.contrib.auth.models import User
from rest_framework import serializers, exceptions

from articles.models import Article, UserProfile, ArtCategory
from articles.tasks import notify_update_article


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        if not (User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists()):
            user = User.objects.create_user(username, email, password)
            return user
        else:
            raise exceptions.ValidationError('User with this username/email already exists')

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(write_only=True, required=True)
    username = serializers.CharField(source='get_username')
    email = serializers.CharField(source='get_email')
    first_name = serializers.CharField(required=False, source='get_first_name')
    last_name = serializers.CharField(required=False, source='get_last_name')

    class Meta:
        model = UserProfile
        fields = ('user', 'username', 'email', 'first_name', 'last_name', 'role')

    def validate_role(self, value):
        if value not in ['translator', 'requester']:
            raise serializers.ValidationError("Role must be translator or requester")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        profile = UserProfile.objects.create(user=user, 
            role=validated_data.pop('role'))
        return profile

class ArticleSerializer(serializers.ModelSerializer):
    """ Serializer only for RequestsApiView """
    """ checks if user is requester """
    status = serializers.IntegerField(required=False)
    reg_date = serializers.DateTimeField(required=False)

    class Meta:
        model = Article
        fields = ('id', 'requester', 'source_text', 'topic_id', 'source_language', \
            'target_language', 'status', 'reg_date', 'translator', 'target_text', \
            'deadline', 'done_date')

    def validate_requester(self, value):
        if value.role != 'requester':
            raise serializers.ValidationError("Only requester can do that!")
        return value

    def create(self, validated_data):
        requester = validated_data.pop('requester')
        source_text = validated_data.pop('source_text')
        topic_id = validated_data.pop('topic_id') #ALREADY ARTCATEGORY OBJECTS!!!!!!!!!!!!!!
        source_language = validated_data.pop('source_language')
        target_language = validated_data.pop('target_language')
        art = Article(requester=requester, source_text=source_text, source_language=source_language, \
            status=0, reg_date=datetime.datetime.now())
        art.save()
        for c in topic_id:
            art.topic_id.add(c)
        for t in target_language:
            art.target_language.add(t)
        art.save()
        return art


class ArticleIdSerializer(serializers.ModelSerializer):
    """ Serializer only for RequestsIdApiView """
    """ checks if user is translator and owns this Article, target_text and status==1"""
    target_text = serializers.CharField(required=True)
    source_text = serializers.CharField(required=False)
    requester = UserProfileSerializer(required=False)
    status = serializers.IntegerField(required=False)
    source_language = serializers.PrimaryKeyRelatedField(many=False, read_only=True, required=False)
    target_language = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)
    topic_id = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)
    reg_date = serializers.DateTimeField(required=False)

    class Meta:
        model = Article
        fields = ('id', 'requester', 'source_text', 'topic_id', 'source_language', \
            'target_language', 'status', 'reg_date', 'translator', 'target_text', \
            'deadline', 'done_date')

    def validate_translator(self, value):
        if value != self.instance.translator:#self.context['request_translator']:
            print (value)
            print (self.instance.translator)
            raise serializers.ValidationError("Only translator that accepted request can finish it!")
        return value

    def validate_status(self, value):
        if value != 1:
            raise serializers.ValidationError("You can only finish request with status=1")
        return value

    def update(self, instance, validated_data):
        instance.target_text =  validated_data.pop('target_text')
        instance.done_date = datetime.datetime.now()
        if instance.status != 1:
            raise serializers.ValidationError("You can only finish request with status = 1")
        instance.status = 2
        instance.save()
        notify_update_article(instance.id).delay()
        return instance

class ArticleAcceptSerializer(serializers.ModelSerializer):
    """ Serializer only for RequestsAcceptApiView """
    """ checks if user is translator, deadline and status==0"""
    deadline = serializers.DateTimeField(required=True)
    target_text = serializers.CharField(required=False)
    source_text = serializers.CharField(required=False)
    requester = UserProfileSerializer(required=False)
    status = serializers.IntegerField(required=False)
    source_language = serializers.PrimaryKeyRelatedField(many=False, read_only=True, required=False)
    target_language = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)
    topic_id = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)
    reg_date = serializers.DateTimeField(required=False)

    class Meta:
        model = Article
        fields = ('id', 'requester', 'source_text', 'topic_id', 'source_language', \
            'target_language', 'status', 'reg_date', 'translator', 'target_text', \
            'deadline', 'done_date')

    def validate_translator(self, value):
        if value.role != 'translator':
            raise serializers.ValidationError("Only translator can accept request")
        return value

    def validate_status(self, value):
        if value != 0:
            raise serializers.ValidationError("You can only accept request with status=0")
        return value

    def update(self, instance, validated_data):
        instance.translator =  validated_data.pop('translator')
        instance.deadline = validated_data.pop('deadline')
        if instance.status != 0:
            raise serializers.ValidationError("You can only accept request with status = 0")
        instance.status = 1
        instance.save()
        notify_update_article(instance.id).delay()
        return instance