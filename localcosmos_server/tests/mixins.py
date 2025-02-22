from django.test import RequestFactory
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from localcosmos_server.models import LocalcosmosUser, App, SecondaryAppLanguages, AppUserRole

from localcosmos_server.datasets.models import Dataset, DatasetImages

from localcosmos_server.tests.common import (TEST_DATASET_DATA_WITH_ALL_REFERENCE_FIELDS, powersetdic,
                                             TEST_DATASET_FULL_GENERIC_FORM, TEST_MEDIA_ROOT, TEST_IMAGE_PATH)

from django.utils import timezone

import os, shutil

class WithUser:

    # allowed special chars; @/./+/-/_
    test_username = 'TestUser@.+-_'
    test_email = 'testuser@localcosmos.org'
    test_password = '#$_><*}{|///0x'

    test_superuser_username = 'TestSuperuser'
    test_superuser_email = 'testsuperuser@localcosmos.org'

    test_first_name = 'First Name'

    def create_user(self):
        user = LocalcosmosUser.objects.create_user(self.test_username, self.test_email, self.test_password)
        return user

    def create_superuser(self):
        superuser = LocalcosmosUser.objects.create_superuser(self.test_superuser_username, self.test_superuser_email,
                                                        self.test_password)
        return superuser
        


class WithApp:

    app_name = 'TestApp'
    app_uid = 'app_for_tests'
    app_primary_language = 'de'
    app_secondary_languages = ['en']

    testapp_relative_www_path = 'app_for_tests/release/webapp/www/'

    # the builder does not create a review folder. the review folder is only for this test suite
    testapp_relative_review_www_path = 'app_for_tests/review/webapp/www/'
    testapp_relative_preview_www_path = 'app_for_tests/preview/www/'
    

    def setUp(self):
        super().setUp()

        self.app = App.objects.create(name=self.app_name, primary_language=self.app_primary_language,
                                      uid=self.app_uid)

        for language in self.app_secondary_languages:
            secondary_language = SecondaryAppLanguages(
                app=self.app,
                language_code=language,
            )

            secondary_language.save()


class WithMedia:

    def clean_media(self):
        if os.path.isdir(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)

        os.makedirs(TEST_MEDIA_ROOT)  

    def setUp(self):
        super().setUp()
        self.clean_media()

    def tearDown(self):
        super().tearDown()
        self.clean_media()



class WithDataset:

    def create_dataset(self):

        dataset = Dataset(
            app_uuid = self.app.uuid,
            data = TEST_DATASET_DATA_WITH_ALL_REFERENCE_FIELDS,
            created_at = timezone.now(),
        )

        dataset.save()

        return dataset

    def create_notaxon_dataset(self):

        dataset_data = TEST_DATASET_DATA_WITH_ALL_REFERENCE_FIELDS
        del dataset_data['dataset']['reported_values']['7e5c9390-61cf-4cb5-8b0f-9086b2f387ce']

        dataset = Dataset(
            app_uuid = self.app.uuid,
            data = dataset_data,
            created_at = timezone.now(),
        )

        dataset.save()

        return dataset


    def create_full_dataset(self):
        
        dataset = Dataset(
            app_uuid = self.app.uuid,
            data = TEST_DATASET_FULL_GENERIC_FORM,
            created_at = timezone.now(),
        )

        dataset.save()

        return dataset


    def create_dataset_image(self, dataset, field_uuid):

        image = SimpleUploadedFile(name='test_image.jpg', content=open(TEST_IMAGE_PATH, 'rb').read(),
                                   content_type='image/jpeg')

        dataset_image = DatasetImages(
            dataset = dataset,
            field_uuid = field_uuid,
            image = image,
        )

        dataset_image.save()

        return dataset_image
        
    

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class WithImageForForm:

    def get_image(self, filename):

        im = Image.new(mode='RGB', size=(200, 200)) # create a new image using PIL
        im_io = BytesIO() # a BytesIO object for saving image
        im.save(im_io, 'JPEG') # save the image to im_io
        im_io.seek(0) # seek to the beginning

        image = InMemoryUploadedFile(
            im_io, None, filename, 'image/jpeg', len(im_io.getvalue()), None
        )

        return image


    def get_zipfile(self, filename):

        im = Image.new(mode='RGB', size=(200, 200)) # create a new image using PIL
        im_io = BytesIO() # a BytesIO object for saving image
        im.save(im_io, 'JPEG') # save the image to im_io
        im_io.seek(0) # seek to the beginning

        zipfile = InMemoryUploadedFile(
            im_io, None, filename, 'application/zip', len(im_io.getvalue()), None
        )

        return zipfile


class WithPowerSetDic:

    def validation_test(self, post_data, required_fields, form_class, **form_kwargs):

        file_keys = form_kwargs.pop('file_keys', [])

        testcases = powersetdic(post_data)

        for post in testcases:

            files = {}
            for key, value in post.items():
                if key in file_keys:
                    files[key] = value

            form = form_class(post, files=files)
            
            keys = set(post.keys())

            form.is_valid()
            
            if required_fields.issubset(keys):
                form.is_valid()
                if not form.is_valid():
                    print(form.errors)
                self.assertEqual(form.errors, {})
                
            else:
                self.assertFalse(form.is_valid())
        
        

from localcosmos_server.datasets.models import DatasetValidationRoutine, DATASET_VALIDATION_CHOICES
class WithValidationRoutine:

    def create_validation_routine(self):

        for counter, tupl in enumerate(DATASET_VALIDATION_CHOICES, 1):

            validation_class = tupl[0]

            step = DatasetValidationRoutine(
                app=self.app,
                validation_class=validation_class,
                position=counter,
            )

            step.save()


from localcosmos_server.online_content.models import (TemplateContent, LocalizedTemplateContent,
    LocalizedDraftImageMicroContent, DraftImageMicroContent, DraftTextMicroContent, LocalizedDraftTextMicroContent)


class WithOnlineContent:

    template_content_title = 'Test template content'
    template_content_navigation_link_name = 'Test navigation link'
    template_type = 'page'
    template_name = 'page/test.html'

    def create_template_content(self, template_name=None, template_type=None):

        if template_name == None:
            template_name = self.template_name

        if template_type == None:
            template_type = self.template_type
        
        self.template_content = TemplateContent.objects.create(self.user, self.app, self.app.primary_language,
                self.template_content_title, self.template_content_navigation_link_name, self.template_name,
                self.template_type)

        self.localized_template_content = LocalizedTemplateContent.objects.get(language=self.app.primary_language,
            template_content=self.template_content)

        return self.template_content


    def create_secondary_language_ltcs(self):

        for language in self.app.secondary_languages():

            draft_title = '{0} {1}'.format(self.template_content_title, language)
            draft_navigation_link_name = '{0} {1}'.format(self.template_content_navigation_link_name, language)

            localized_template_content = LocalizedTemplateContent.objects.create(self.user, self.template_content,
                language, draft_title, draft_navigation_link_name)


    def create_draft_image_microcontent(self, template_content, microcontent_type, language):

        im = Image.new(mode='RGB', size=(200, 200)) # create a new image using PIL
        im_io = BytesIO() # a BytesIO object for saving image
        im.save(im_io, 'JPEG') # save the image to im_io
        im_io.seek(0) # seek to the beginning

        image = InMemoryUploadedFile(
            im_io, None, 'draft_image.jpg', 'image/jpeg', len(im_io.getvalue()), None
        )

        draft_imc = DraftImageMicroContent(
            template_content = template_content,
            microcontent_type = microcontent_type,
        )

        draft_imc.save()
        
        draft_limc = LocalizedDraftImageMicroContent(
            microcontent = draft_imc,
            content = image,
            language = language,
        )

        draft_limc.save()

        return draft_limc


    def create_draft_microcontent(self, template_content, microcontent_type, language):
        
        draft_mc = DraftTextMicroContent(
            template_content = template_content,
            microcontent_type = microcontent_type,
        )

        draft_mc.save()
        
        
        draft_lmc = self.create_localized_draft_microcontent(draft_mc, language)

        return draft_lmc

    def create_localized_draft_microcontent(self, microcontent, language):

        draft_lmc = LocalizedDraftTextMicroContent(
            microcontent = microcontent,
            content = 'test atomic content {0}'.format(language),
            language = language,
        )

        draft_lmc.save()

        return draft_lmc
    

    def get_view(self, view_class, url_name):
        
        url_kwargs = self.get_url_kwargs()
        
        request = self.factory.get(reverse(url_name, kwargs=url_kwargs))
        request.session = self.client.session
        request.app = self.app
        request.user = self.user

        view = view_class()
        view.request = request
        view.app = self.app
        view.app_disk_path = self.app.get_installed_app_path(app_state='published')
        view.kwargs = url_kwargs

        return view, request
        
        
    

class CommonSetUp:
    
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

        self.user = self.create_user()

        self.role = AppUserRole(
            app=self.app,
            user = self.user,
            role='admin',
        )

        self.superuser = self.create_superuser()

        self.role.save()

        self.client.login(username=self.test_superuser_username, password=self.test_password)
