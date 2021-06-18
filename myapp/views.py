from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from .models import Questions,Answers

class index(View):
    def get(self,request):
        qss = Questions.objects.all()
        content = {'qs':qss}
        return render(request,'myapp/index.html',context=content)

    def post(self,request):
        qs_id = request.POST.get('questions')
        obj_qs = Questions.objects.get(pk=qs_id)
        qs = obj_qs.question
        img = request.FILES.get('image')
        ans = Answers(question=obj_qs,answer=request.POST.get('answer'),image=img)
        ans.save()
        content = {'qs_id':qs_id,'ans': ans.answer,'image':ans.image,'qs':qs}
        return render(request,'myapp/save.html',context=content)

