from django import forms
from .models import Transaction
from accounts.models import UserBankAccount
from transactions.constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID,TRANSFER
from  django.core.mail import EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string

def send_email(user,amount,subject,template):
    message = render_to_string(template,{'user': user,'amount':amount })
    send_email =EmailMultiAlternatives(subject,"",to =[user.email])
    send_email.attach_alternative(message,"text/html")
    send_email.send()


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account') # account value ke pop kore anlam
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True # ei field disable thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput() # user er theke hide kora thakbe

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self): # amount field ke filter korbo
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount') # user er fill up kora form theke amra amount field er value ke niye aslam
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance # 1000
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance: # amount = 5000, tar balance ache 200
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount



class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount
    

class TransferForm(TransactionForm):
    recived_account_no = forms.IntegerField()

    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type',
            'recived_account_no'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True  # Disable the field
        self.fields['transaction_type'].widget = forms.HiddenInput()  # Hide the field from the user

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        if amount > self.account.balance:
            raise forms.ValidationError(f'Insufficient funds. Your balance is {self.account.balance}.')
        return amount
    
    def clean_recived_account_no(self):
        account_no = self.cleaned_data.get('recived_account_no')
        try:
            received_account = UserBankAccount.objects.get(account_no=account_no)
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError('Recipient account not found.')
        self.cleaned_data['received_account'] = received_account
        return account_no
    
    def save(self, commit=True):
        transaction = super().save(commit=False)
        received_account = self.cleaned_data.get('received_account')
        
        transaction.balance_after_transaction = self.account.balance - transaction.amount
        if commit:
            transaction.save()
            self.account.balance -= transaction.amount
            self.amount =transaction.amount
            send_email(self.account.user,self.amount,"transfer amount","transactions/user_transfer_email.html")
            self.account.save()
            received_account.balance += transaction.amount
            send_email(received_account.user,self.amount,"transfer amount","transactions/recived.html")
            received_account.save()
        return transaction



        

