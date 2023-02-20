import os
import re
from git import Repo

# Specify the URL of the Git repository and the local directory to clone it to
repo_url = 'https://github.com/woocommerce/woocommerce.git'
local_dir = './repository'
results_dir = './templates'

template_version_regex = re.compile(r"\* @version\s+(.*)")

# Clone the Git repository
print('Cloning repository')
Repo.clone_from(repo_url, local_dir)

# Open the cloned repository
repo = Repo(local_dir)
repo.config_writer().set_value("core", "protectNTFS ", "false").release()

templates_found = []

# Iterate over the specified tags
for tag in repo.tags:
    # remove v from tag
    tag_name = tag.name.replace('v', '')
    try:
      major_version = int(tag_name.split('.')[0])
    except:
      print('Failed to get major version from tag {}. Skipping...'.format(tag_name))
      continue

    # Start from version 2
    if major_version < 2:
      continue

    template_location = 'plugins/woocommerce/templates/' if major_version >= 6 else 'templates/'

    # Checkout the tag to get the files
    try:  
      print('Downloading files from tag {}'.format(tag_name))
      repo.git.checkout(tag)
    except:
      print('Failed to checkout tag {}. Skipping...'.format(tag_name))
      continue

    template_tag_search = '* @version {}'.format(tag_name)

    # Copy the files from the repository to the tag folder
    for file in repo.tree().traverse():
        if file.type == 'blob' and file.path.startswith(template_location):
            try:
              file_content = repo.git.show('{}:{}'.format(tag_name, file.path))
            except:
              print('Failed to get file content for file {}. Skipping...'.format(file.path))
              continue
            
            # Skip if version is not current tag. This means the file is not updated in this version. 
            matches = template_version_regex.search(file_content)
            if not matches:
              continue

            version = matches.group(1)

            file_name = file.path.replace(template_location, '').replace('.php', '.php/{}.php'.format(version))

            # Check template already found
            if file_name in templates_found:
              continue

            templates_found.append(file_name)

            file_path = os.path.join(results_dir, file_name)
            
            # Create the folder if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                print('Writing file {}'.format(file_path))
                f.write(file_content.encode())