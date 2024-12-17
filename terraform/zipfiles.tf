# Lambda Lauer

# Null resource to prepare Lambda package (zip) for pandas
resource "null_resource" "prepare_packages" {
  provisioner "local-exec" {
    command = <<EOT
    # remove layer package
    rm -rf ${var.build_path}

    # creaate directories to layer
    mkdir -p ${var.build_path}/python/lib/${var.python_runtime}/site-packages
    # Create package dependencies to pandas
    pip3 install -r ${var.code_path}/pandas.txt -t ${var.build_path}/python/lib/${var.python_runtime}/site-packages
    # Create the zip files to pandas package
    cd ${var.build_path}
    zip -r pandas.zip python/*

    # remove python package for pandas to recreate to requests
    rm -rf python
    mkdir -p ${var.build_path}/python/lib/${var.python_runtime}/site-packages
    # Create the dependencies for requests
    pip3 install -r ${var.code_path}/requests.txt -t ${var.build_path}/python/lib/${var.python_runtime}/site-packages
    # Create the zip file to requests
    cd ${var.build_path}
    zip -r requests.zip python/*

   # remove python package to create Psycopg2
    rm -rf python
    mkdir -p ${var.build_path}/python/lib/${var.python_runtime}/site-packages

   # Instala o psycopg2-binary compatível com o AWS Lambda
     pip3 install --platform manylinux2014_x86_64 \
     --target ${var.build_path}/python/lib/${var.python_runtime}/site-packages \
     --python-version 3.12 \
     --only-binary=:all: \
     psycopg2-binary

   # Compacta o diretório python em um arquivo ZIP
   cd ${var.build_path}
   zip -r psycopg2.zip python/*

    * remover python package to clean
    rm -rf python

    EOT
    }

  triggers = {
    build_trigger = timestamp()
  }
}

# Null resource to prepare Lambda code package (zip)
resource "null_resource" "prepare_lambda" {
  provisioner "local-exec" {
    command = <<EOT
    # excluir o arquivo, caso exista
    rm ${var.code_path}/code.zip

    # Criar o arquivo zip apenas com os codigos
    cd ${var.code_path}
    zip -r code.zip .

    EOT
    }

  triggers = {
    build_trigger = timestamp()
  }
}
