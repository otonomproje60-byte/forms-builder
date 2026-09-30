/**
 * Forms Builder Embeddable Widget
 * Usage: <script src="https://your-domain.com/static/embed.js" data-form-id="FORM_ID"></script>
 * Or: <div id="forms-builder-FORM_ID"></div><script src="https://your-domain.com/static/embed.js" data-form-id="FORM_ID"></script>
 */
(function() {
  'use strict';

  var script = document.currentScript || document.querySelector('script[data-form-id]');
  if (!script) return;

  var formId = script.getAttribute('data-form-id');
  var apiBase = script.getAttribute('data-api-base') || '';
  var containerId = script.getAttribute('data-container-id') || 'forms-builder-' + formId;

  if (!formId) {
    console.error('Forms Builder: data-form-id attribute required');
    return;
  }

  var container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement('div');
    container.id = containerId;
    script.parentNode.insertBefore(container, script.nextSibling);
  }

  var cssUrl = apiBase + '/static/embed.css';
  if (!document.querySelector('link[href="' + cssUrl + '"]')) {
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = cssUrl;
    document.head.appendChild(link);
  }

  function loadForm() {
    fetch(apiBase + '/embed/' + formId)
      .then(function(r) { return r.text(); })
      .then(function(html) {
        container.innerHTML = html;
        var form = container.querySelector('form');
        if (form) {
          initForm(form, apiBase, formId);
        }
      })
      .catch(function(err) {
        console.error('Forms Builder: Failed to load form', err);
        container.innerHTML = '<div style="color:#e74c3c;padding:20px;text-align:center;">Failed to load form</div>';
      });
  }

  function initForm(form, apiBase, formId) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var submitBtn = form.querySelector('button[type="submit"]');
      var formData = new FormData(form);
      var data = Object.fromEntries(formData.entries());

      form.querySelectorAll('.error-message').forEach(function(el) { el.textContent = ''; });
      form.querySelectorAll('.form-group').forEach(function(el) { el.classList.remove('error'); });

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="forms-builder-loading"></span>Submitting...';
      }

      fetch(apiBase + '/api/forms/' + formId + '/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: data })
      })
      .then(function(r) { return r.json(); })
      .then(function(resp) {
        if (resp.id) {
          form.innerHTML = '<div class="forms-builder-success"><h2>✓ Thank you!</h2><p>Your submission has been received.</p></div>';
        } else {
          if (resp.detail) {
            if (typeof resp.detail === 'string') {
              alert('Error: ' + resp.detail);
            } else if (resp.detail.errors) {
              resp.detail.errors.forEach(function(err) {
                var field = form.querySelector('[data-field="' + err.loc[1] + '"]');
                if (field) {
                  field.classList.add('error');
                  var msgEl = field.querySelector('.error-message');
                  if (msgEl) msgEl.textContent = err.msg;
                }
              });
            }
          } else {
            alert('Submission failed. Please try again.');
          }
        }
      })
      .catch(function(err) {
        console.error('Forms Builder: Submission error', err);
        alert('Network error. Please try again.');
      })
      .finally(function() {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Submit';
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadForm);
  } else {
    loadForm();
  }
})();