
  function resetPassword(userId, username) {
      const newPass = prompt(`Enter new password for ${username}:`);
      if(newPass) {
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = `/admin/reset_password/${userId}`;
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = 'new_password';
          input.value = newPass;
          form.appendChild(input);
          document.body.appendChild(form);
          form.submit();
      }
  }
