package Ejercicio_06;

public class Celador extends Personal {
    private int numeroEntrada;

    public Celador(String dni, String nombre, String direccion, String telefono, double sueldo, String nroSeguridadSocial, int numeroEntrada) {
        super(dni, nombre, direccion, telefono, sueldo, nroSeguridadSocial);
        this.numeroEntrada = numeroEntrada;
    }

    public int getNumeroEntrada() {
        return numeroEntrada;
    }

    public void setNumeroEntrada(int numeroEntrada) {
        this.numeroEntrada = numeroEntrada;
    }

    public void registrarVisita(Visitante visitante) {
        System.out.println("Celador " + this.nombre + " registra visita de: " + visitante.getNombre() + " en la entrada N° " + this.numeroEntrada);
    }
}
