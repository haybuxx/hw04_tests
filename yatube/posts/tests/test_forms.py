from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post
from ..forms import PostForm

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username='post_author',
        )

        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth'),
            text='Тестовая запись для создания 1 поста',
            group=cls.group)

        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_author)

    def test_create_post(self):
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.pk
        }
        count_posts = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        group=form_data['group'],
                        author=self.post_author
                        ).exists())
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'post_author'}))

    def test_create_post_not_authorized(self):
        form_data = {
            'text': 'form_data',
            'group': 'Группа'
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
                         text='Текст'
                         ).exists())

    def test_edit_post(self):
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author)
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id}
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id}))
        post_one = Post.objects.latest('id')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_one.text, form_data['text'])
        self.assertEqual(post_one.author, self.post_author)
        self.assertEqual(post_one.group_id, form_data['group'])

    def test_edit_post_not_authorized(self):
        form_data = {'text': 'Новый текст',
                     'group': self.group.pk,
                     }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        obj = self.post
        obj.refresh_from_db()
        self.assertNotEqual(obj.text, form_data['text'])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_no_edit_post_not_author(self):
        posts_count = Post.objects.count()
        form_data = {'text': 'Новый текст',
                     'group': self.group,
                     'author': 'Новый автор'}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        post = Post.objects.get(id=self.post.pk)
        checked_post = {'text': post.text,
                        'group': post.group,
                        'author': post.author}
        self.assertNotEqual(form_data, checked_post)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error_name2 = 'Поcт добавлен в базу данных по ошибке'
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            error_name2)
