from celery.task import task

from correspondence.models import Mailing, Letter

@task
def generate_collation_task(mailing_id, redirect):
    mailing = Mailing.objects.get(pk=mailing_id)
    mailing.get_file()
    return redirect

@task
def generate_letter_task(letter_id):
    letter = Letter.objects.get(pk=letter_id)
    return letter.get_file()

@task
def combine_pdfs_task(pdf_files):
    from correspondence import utils
    combined = utils.combine_pdfs(pdf_files)
    return combined


