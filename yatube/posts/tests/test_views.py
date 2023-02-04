from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания поста',
            group=Group.objects.create(
                title='Заголовок для тестовой группы',
                slug='slug'))

        cls.postTwo = Post.objects.create(
            author=cls.user,
            text='Тестовая запись 2 для создания поста',
            group=Group.objects.create(
                title='Заголовок 2 для тестовой группы',
                slug='slug2'))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (reverse('posts:group_posts',
                                              kwargs={'slug': 'slug'})),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': 'auth'}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.pk}),
            'posts/create_post.html':
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),

        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_correct_template(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][1]
        context_objects = {
            first_object.author.username: self.post.author.username,
            first_object.text: self.post.text,
            first_object.group.title: self.post.group.title,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_group_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                              kwargs={'slug':
                                                      self.post.group.slug
                                                      }))
        first_object = response.context['page_obj'][0]
        self.assertEqual(self.post.group.title,
                         first_object.group.title)
        self.assertEqual(self.post.group.slug, first_object.group.slug)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      f'{self.user.username}'
                                                      }))
        first_object = response.context['page_obj'][1]
        self.assertEqual(response.context['author'].username, f'{self.user}')
        self.assertEqual(first_object.text,
                         self.post.text)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.pk}))
        self.assertEqual(response.context['post1'], self.post.text)

    def test_create_post_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              self.post.pk}))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                              kwargs={'slug': 'slug'}))
        first_object = response.context['page_obj'][0]
        self.assertTrue(self.postTwo.text, first_object.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth',)

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='slug',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse('posts:index'): 'index',
            reverse('posts:group_posts',
                    kwargs={'slug': 'slug'}): 'group_posts',
            reverse('posts:profile', kwargs={'username': 'auth'}): 'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse('posts:index') + "?page=2": 'index',
            reverse('posts:group_posts', kwargs={'slug': 'slug'}) + "?page=2":
            'group_posts',
            reverse('posts:profile', kwargs={'username': 'auth'}) + "?page=2":
            'profile',
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj')), 3)
