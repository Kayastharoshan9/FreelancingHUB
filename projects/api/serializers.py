from rest_framework import serializers
from projects.models import Project, Tag, Review, Job, Bid, Milestone, ClientReview, FreelancerReview, Payment
from users.models import Profile


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer(many=False)
    tags = TagSerializer(many=True)
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_reviews(self, obj):
        reviews = obj.review_set.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data


class BidSerializer(serializers.ModelSerializer):
    freelancer = ProfileSerializer(many=False, read_only=True)
    
    class Meta:
        model = Bid
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer(many=False, read_only=True)
    required_skills = TagSerializer(many=True, read_only=True)
    bids = serializers.SerializerMethodField()
    milestones = MilestoneSerializer(many=True, read_only=True)
    
    class Meta:
        model = Job
        fields = '__all__'
    
    def get_bids(self, obj):
        bids = obj.bids.all()
        serializer = BidSerializer(bids, many=True)
        return serializer.data


class ClientReviewSerializer(serializers.ModelSerializer):
    reviewer = ProfileSerializer(many=False, read_only=True)
    freelancer = ProfileSerializer(many=False, read_only=True)
    
    class Meta:
        model = ClientReview
        fields = '__all__'


class FreelancerReviewSerializer(serializers.ModelSerializer):
    reviewer = ProfileSerializer(many=False, read_only=True)
    client = ProfileSerializer(many=False, read_only=True)
    
    class Meta:
        model = FreelancerReview
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
