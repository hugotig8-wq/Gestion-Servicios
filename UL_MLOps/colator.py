#Su responsabilidad sería construir el batch.
#Actualmente el DataLoader utiliza el collator por defecto de PyTorch.
#Pero en los LLM es habitual usar un DataCollator personalizado que:
#haga el padding dinámico;
#prepare correctamente las labels;
#optimice la memoria.
#Más adelante probablemente querremos implementar uno.
