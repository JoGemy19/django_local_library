import datetime
from django.shortcuts import render , get_object_or_404
from .models import Book,BookInstance,Author,Genre,Language
from django.views import generic
from django.contrib.auth.decorators import login_required , permission_required
from django.contrib.auth.mixins import LoginRequiredMixin , PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django .urls import reverse , reverse_lazy
from catalog.forms import RenewBookForm
from django.views.generic.edit import CreateView , UpdateView , DeleteView


@login_required
def index(request):
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact = 'a').count()
    num_authors = Author.objects.count()
    books_contain_Man = Book.objects.filter(title__contains = "The").count()
    num_visits = request.session.get('num_visits',1)
    request.session['num_visits']= num_visits +1
    context = {
        'num_books' : num_books,
        'num_instances':num_instances,
        "num_instances_available" : num_instances_available,
        "num_authors": num_authors,
        "books_contain_Man" : books_contain_Man,
        "num_visits" : num_visits,
    }
    return render(request,"index.html",context=context)

class BooksListView(generic.ListView):
    model = Book
    paginate_by = 2
    
class BooksDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 2

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact = 'o').order_by('due_back')

class AllBorowrredBooksListView(PermissionRequiredMixin,generic.ListView):
    permission_required = "catalog.can_mark_returned"
    model = BookInstance
    template_name = 'catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10
    def get_queryset(self):
        return BookInstance.objects.filter(status__exact = 'o').order_by("due_back")
    
    
@login_required
@permission_required("catalog.can_mark_returned",raise_exception=True)
def renew_book_librarian(request , pk):
    book_instance = get_object_or_404(BookInstance , pk = pk)
    
    if request.method == "POST":
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data["renewal_date"]
            book_instance.save()
            return HttpResponseRedirect(reverse("all-borrowed"))
    else :
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={"renewal_date":proposed_renewal_date})
    context= {
        "form" : form,
        "book_instance" : book_instance
    }
    return render(request,"catalog/book_renew_librarian.html",context)

class AuthorCreate(PermissionRequiredMixin,CreateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth',"date_of_death"]
    initial = {'date_of_death':datetime.date.today}
    permission_required = "catalog.add_author"
    
class AuthorUpdate(PermissionRequiredMixin,UpdateView):
    model = Author
    fields = "__all__"
    permission_required = "catalog.change_author"
    
class AuthorDelete(PermissionRequiredMixin,DeleteView):
    model = Author
    success_url = reverse_lazy("authors")
    permission_required = "catalog.delete_author"
    def form_valid(self, form):
        try :
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e :
            return HttpResponseRedirect("author-delete",kwargs={"pk":self.object.pk})

class BookCreate(PermissionRequiredMixin,CreateView):
    model = Book
    fields = "__all__"
    permission_required = "catalog.add_book"
    
class BookUpdate(PermissionRequiredMixin,UpdateView):
    model = Book
    fields = "__all__"
    permission_required = "catalog.change_book"
    
class BookDelete(PermissionRequiredMixin,DeleteView):
    model = Book
    success_url = reverse_lazy("books")
    permission_required = "catalog.delete_author"
    def form_valid(self,form):
        try :
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect("book-delete",kwargs ={"pk":self.objects.pk})
