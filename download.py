import os
import re
from git import Repo
import json

use_existing_repo = True

# Specify the URL of the Git repository and the local directory to clone it to
repo_url = 'https://github.com/woocommerce/woocommerce.git'
local_dir = './repository'
results_dir = './templates'

template_version_regex = re.compile(r"\* @version\s+(.*)")

# Clone the Git repository
if not use_existing_repo:
  print('Cloning repository')
  Repo.clone_from(repo_url, local_dir)

# Open the cloned repository
repo = Repo(local_dir)
repo.config_writer().set_value("core", "protectNTFS ", "false").release()

templates_found = []

meta = {}

tags = repo.tags
versions = [tag.name for tag in tags if re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', tag.name)]
versions.reverse()

print('Getting tags: {}'.format(versions))

# For debugging, only take the first 5 tags
# versions = versions[:5]


# Iterate over the specified tags
for tag_name in versions:
    major_version = int(tag_name.split('.')[0])

    if major_version < 3:
      continue  # Skip versions before 3.0.0

    template_location = 'plugins/woocommerce/templates/' if major_version >= 6 else 'templates/'

    # Checkout the tag to get the files
    try:  
      print('Downloading files from tag {}'.format(tag_name))
      repo.git.checkout(tag_name)
    except:
      print('Failed to checkout tag {} Skipping...'.format(tag_name))
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

            original_template_path = file.path.replace(template_location, '')
            file_name = original_template_path.replace('.php', '.php/{}.php'.format(version))

            # Check template already found
            if file_name in templates_found:
              continue

            templates_found.append(file_name)

            file_path = os.path.join(results_dir, file_name)
            
            # Create the folder if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Add version to meta
            if original_template_path not in meta:
              meta[original_template_path] = { 'versions': [] }

            meta[original_template_path]['versions'].append(version)

            # TODO: Add to metadata if template is deleted on a later version
            
            with open(file_path, 'wb') as f:
                print('Writing file {}'.format(file_path))
                f.write(file_content.encode())


# Write meta file
with open('./meta.json', 'w') as f:
  print('Writing meta file')
  f.write(json.dumps({ 
    'versions': versions.reverse(), 
    'templates': meta 
  }))

print('Done')